# Created By: Virgil Dupras
# Created On: 2009-12-30
# Copyright 2015 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from optparse import OptionParser
import json

from hscommon.plat import ISOSX

def main(options):
    if options.edition not in {'se', 'me', 'pe'}:
        options.edition = 'se'
    if options.ui not in {'cocoa', 'qt'}:
        options.ui = 'cocoa' if ISOSX else 'qt'
    build_type = 'Dev' if options.dev else 'Release'
    print("Configuring dupeGuru {0} for UI {1} ({2})".format(options.edition.upper(), options.ui, build_type))
    conf = {
        'edition': options.edition,
        'ui': options.ui,
        'dev': options.dev,
    }
    json.dump(conf, open('conf.json', 'w'))

if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        '--edition', dest='edition',
        help="dupeGuru edition to build (se, me or pe). Default is se."
    )
    parser.add_option(
        '--ui', dest='ui',
        help="Type of UI to build. 'qt' or 'cocoa'. Default is determined by your system."
    )
    parser.add_option(
        '--dev', action='store_true', dest='dev', default=False,
        help="If this flag is set, will configure for dev builds."
    )
    (options, args) = parser.parse_args()
    main(options)

