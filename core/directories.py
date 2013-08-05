# Created By: Virgil Dupras
# Created On: 2006/02/27
# Copyright 2013 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

from xml.etree import ElementTree as ET
import logging
from pathlib import Path

from jobprogress import job
from hscommon.util import FileOrPath

from . import fs

class DirectoryState:
    Normal = 0
    Reference = 1
    Excluded = 2

class AlreadyThereError(Exception):
    """The path being added is already in the directory list"""

class InvalidPathError(Exception):
    """The path being added is invalid"""

class Directories:
    #---Override
    def __init__(self, fileclasses=[fs.File]):
        self._dirs = []
        self.states = {}
        self.fileclasses = fileclasses
    
    def __contains__(self, path):
        for p in self._dirs:
            if path == p or p in path.parents():
                return True
        return False
    
    def __delitem__(self,key):
        self._dirs.__delitem__(key)
    
    def __getitem__(self,key):
        return self._dirs.__getitem__(key)
    
    def __len__(self):
        return len(self._dirs)
    
    #---Private
    def _default_state_for_path(self, path):
        # Override this in subclasses to specify the state of some special folders.
        if path.name.startswith('.'): # hidden
            return DirectoryState.Excluded
    
    def _get_files(self, from_path, j):
        j.check_if_cancelled()
        state = self.get_state(from_path)
        if state == DirectoryState.Excluded:
            # Recursively get files from folders with lots of subfolder is expensive. However, there
            # might be a subfolder in this path that is not excluded. What we want to do is to skim
            # through self.states and see if we must continue, or we can stop right here to save time
            if not any(p.parts[:len(from_path.parts)] == from_path.parts for p in self.states):
                return
        try:
            filepaths = set()
            if state != DirectoryState.Excluded:
                found_files = fs.get_files(from_path, fileclasses=self.fileclasses)
                logging.debug("Collected %d files in folder %s", len(found_files), str(from_path))
                for file in found_files:
                    file.is_ref = state == DirectoryState.Reference
                    filepaths.add(file.path)
                    yield file
            # it's possible that a folder (bundle) gets into the file list. in that case, we don't want to recurse into it
            subfolders = [p for p in from_path.glob('*') if not p.is_symlink() and p.is_dir() and p not in filepaths]
            for subfolder in subfolders:
                for file in self._get_files(subfolder, j):
                    yield file
        except (EnvironmentError, fs.InvalidPath):
            pass
    
    def _get_folders(self, from_folder, j):
        j.check_if_cancelled()
        try:
            for subfolder in from_folder.subfolders:
                for folder in self._get_folders(subfolder, j):
                    yield folder
            state = self.get_state(from_folder.path)
            if state != DirectoryState.Excluded:
                from_folder.is_ref = state == DirectoryState.Reference
                logging.debug("Yielding Folder %r state: %d", from_folder, state)
                yield from_folder
        except (EnvironmentError, fs.InvalidPath):
            pass
    
    #---Public
    def add_path(self, path):
        """Adds 'path' to self, if not already there.
        
        Raises AlreadyThereError if 'path' is already in self. If path is a directory containing
        some of the directories already present in self, 'path' will be added, but all directories
        under it will be removed. Can also raise InvalidPathError if 'path' does not exist.
        """
        if path in self:
            raise AlreadyThereError()
        if not path.exists():
            raise InvalidPathError()
        self._dirs = [p for p in self._dirs if p not in path]
        self._dirs.append(path)
    
    @staticmethod
    def get_subfolders(path):
        """returns a sorted list of paths corresponding to subfolders in `path`"""
        try:
            names = [p.name for p in path.glob('*') if p.is_dir()]
            names.sort(key=lambda x:x.lower())
            return [path[name] for name in names]
        except EnvironmentError:
            return []
    
    def get_files(self, j=job.nulljob):
        """Returns a list of all files that are not excluded.
        
        Returned files also have their 'is_ref' attr set.
        """
        for path in self._dirs:
            for file in self._get_files(path, j):
                yield file
    
    def get_folders(self, j=job.nulljob):
        """Returns a list of all folders that are not excluded.
        
        Returned folders also have their 'is_ref' attr set.
        """
        for path in self._dirs:
            from_folder = fs.Folder(path)
            for folder in self._get_folders(from_folder, j):
                yield folder
    
    def get_state(self, path):
        """Returns the state of 'path' (One of the STATE_* const.)
        """
        if path in self.states:
            return self.states[path]
        default_state = self._default_state_for_path(path)
        if default_state is not None:
            return default_state
        parent = path.parent()
        if parent in self:
            return self.get_state(parent)
        else:
            return DirectoryState.Normal
    
    def has_any_file(self):
        try:
            next(self.get_files())
            return True
        except StopIteration:
            return False
    
    def load_from_file(self, infile):
        try:
            root = ET.parse(infile).getroot()
        except Exception:
            return
        for rdn in root.getiterator('root_directory'):
            attrib = rdn.attrib
            if 'path' not in attrib:
                continue
            path = attrib['path']
            try:
                self.add_path(Path(path))
            except (AlreadyThereError, InvalidPathError):
                pass
        for sn in root.getiterator('state'):
            attrib = sn.attrib
            if not ('path' in attrib and 'value' in attrib):
                continue
            path = attrib['path']
            state = attrib['value']
            self.set_state(Path(path), int(state))
    
    def save_to_file(self, outfile):
        with FileOrPath(outfile, 'wb') as fp:
            root = ET.Element('directories')
            for root_path in self:
                root_path_node = ET.SubElement(root, 'root_directory')
                root_path_node.set('path', str(root_path))
            for path, state in self.states.items():
                state_node = ET.SubElement(root, 'state')
                state_node.set('path', str(path))
                state_node.set('value', str(state))
            tree = ET.ElementTree(root)
            tree.write(fp, encoding='utf-8')
    
    def set_state(self, path, state):
        if self.get_state(path) == state:
            return
        # we don't want to needlessly fill self.states. if get_state returns the same thing
        # without an explicit entry, remove that entry
        if path in self.states:
            del self.states[path]
            if self.get_state(path) == state: # no need for an entry
                return
        self.states[path] = state
    
