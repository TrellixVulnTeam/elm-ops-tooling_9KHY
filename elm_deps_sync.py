#! /usr/bin/env python
from __future__ import print_function

import sys
import argparse

import elm_package


def sync_versions(top_level_file, spec_file, quiet=False, dry=False, note_test_deps=True):
    """ first file should be the top level elm-package.json.
        second file should be the spec level elm-package.json.
    """

    with open(top_level_file) as f:
        top_level = elm_package.load(f)

    with open(spec_file) as f:
        spec = elm_package.load(f)

    (messages, new_deps) = elm_package.sync_deps(top_level['dependencies'], spec['dependencies'])
    spec['dependencies'] = new_deps

    if note_test_deps:
        test_deps = {}

        for (package_name, package_version) in spec['dependencies'].items():
            if package_name not in top_level['dependencies']:
                test_deps[package_name] = package_version
        spec['test-dependencies'] = elm_package.sorted_deps(test_deps)

    if len(messages) == 0 and not note_test_deps:
        print('No changes needed.')
        return

    print('{number} packages changed.'.format(number=len(messages)))

    if not quiet:
        print('\n'.join(messages))

    if dry:
        print("No changes written.")
        return

    with open(spec_file, 'w') as f:
        elm_package.dump(spec, f)


def main():

    parser = argparse.ArgumentParser(description='Sync deps between a parent and a sub')

    parser.add_argument('--quiet', '-q', action='store_true', help='don\'t print anything', default=False)
    parser.add_argument('--dry', '-d', action='store_true', help='only print possible changes', default=False)
    parser.add_argument('--note',
        action='store_true',
        help='add a test-dependencies field of things only found in the test',
        default=False
    )


    parser.add_argument('top_level_file')
    parser.add_argument('spec_file')
    args = parser.parse_args()

    sync_versions(args.top_level_file, args.spec_file, quiet=args.quiet, dry=args.dry, note_test_deps=args.note)


if __name__ == '__main__':
    main()
