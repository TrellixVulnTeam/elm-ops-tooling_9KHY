#! /usr/bin/env python
from __future__ import print_function

import sys
import argparse

import elm_package
import exact_dependencies


def sync_versions(top_level_file, spec_file, quiet=False, dry=False, note_test_deps=True):
    """ first file should be the top level elm-native-package.json.
        second file should be the spec level elm-native-package.json.
    """

    with open(top_level_file) as f:
        top_level = exact_dependencies.load(f)

    with open(spec_file) as f:
        spec = exact_dependencies.load(f)

    (messages, new_deps) = elm_package.sync_deps(top_level, spec)
    spec = new_deps

    if len(messages) > 0:
        print('{number} packages changed.'.format(number=len(messages)))

        if not dry:
            with open(spec_file, 'w') as f:
                exact_dependencies.dump(spec, f)
        else:
            print("No changes written.")

        if not quiet:
            print('\n'.join(messages))
    else:
        print('No changes needed.')


def main():

    parser = argparse.ArgumentParser(description='Sync deps between a parent and a sub')

    parser.add_argument('--quiet', '-q', action='store_true', help='don\'t print anything', default=False)
    parser.add_argument('--dry', '-d', action='store_true', help='only print possible changes', default=False)
    parser.add_argument('top_level_file')
    parser.add_argument('spec_file')
    args = parser.parse_args()

    sync_versions(args.top_level_file, args.spec_file, quiet=args.quiet, dry=args.dry)


if __name__ == '__main__':
    main()
