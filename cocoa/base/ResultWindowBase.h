/* 
Copyright 2015 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "GPLv3" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.gnu.org/licenses/gpl-3.0.html
*/

#import <Cocoa/Cocoa.h>
#import <Quartz/Quartz.h>
#import "StatsLabel.h"
#import "ResultTable.h"
#import "ProblemDialog.h"
#import "DeletionOptions.h"
#import "HSTableView.h"
#import "PyDupeGuru.h"

@class AppDelegateBase;

@interface ResultWindowBase : NSWindowController
{
@protected
    NSSegmentedControl *optionsSwitch;
    NSToolbarItem *optionsToolbarItem;
    HSTableView *matches;
    NSTextField *stats;
    NSSearchField *filterField;
    
    AppDelegateBase *app;
    PyDupeGuru *model;
    ResultTable *table;
    StatsLabel *statsLabel;
    ProblemDialog *problemDialog;
    DeletionOptions *deletionOptions;
    QLPreviewPanel* previewPanel;
}

@property (readwrite, retain) NSSegmentedControl *optionsSwitch;
@property (readwrite, retain) NSToolbarItem *optionsToolbarItem;
@property (readwrite, retain) HSTableView *matches;
@property (readwrite, retain) NSTextField *stats;
@property (readwrite, retain) NSSearchField *filterField;

- (id)initWithParentApp:(AppDelegateBase *)app;

/* Virtual */
- (void)initResultColumns;
- (void)setScanOptions;

/* Helpers */
- (void)fillColumnsMenu;
- (void)updateOptionSegments;
- (void)showProblemDialog;
- (void)adjustUIToLocalization;

/* Actions */
- (void)changeOptions;
- (void)copyMarked;
- (void)trashMarked;
- (void)filter;
- (void)focusOnFilterField;
- (void)ignoreSelected;
- (void)invokeCustomCommand;
- (void)markAll;
- (void)markInvert;
- (void)markNone;
- (void)markSelected;
- (void)moveMarked;
- (void)openClicked;
- (void)openSelected;
- (void)removeMarked;
- (void)removeSelected;
- (void)renameSelected;
- (void)reprioritizeResults;
- (void)resetColumnsToDefault;
- (void)revealSelected;
- (void)saveResults;
- (void)startDuplicateScan;
- (void)switchSelected;
- (void)toggleColumn:(id)sender;
- (void)toggleDelta;
- (void)toggleDetailsPanel;
- (void)togglePowerMarker;
- (void)toggleQuicklookPanel;
@end
