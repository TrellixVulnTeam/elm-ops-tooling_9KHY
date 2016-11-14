#! /usr/bin/env python
from __future__ import print_function

import sys
from collections import OrderedDict
import json
import argparse


def sync_versions(top_level_file, spec_file, quiet=False, dry=False, note_test_deps=True):
    """ first file should be the top level elm-package.json
        second file should be the spec file
    """

    with open(top_level_file) as f:
        top_level = json.load(f)

    with open(spec_file) as f:
        spec = json.load(f, object_pairs_hook=OrderedDict)

    messages = []

    for (package_name, package_version) in top_level['dependencies'].items():
        if package_name not in spec['dependencies']:
            spec['dependencies'][package_name] = package_version

            messages.append('Package {package_name} inserted to {spec_file} for the first time at version "{package_version}"'.format(
                package_name=package_name, spec_file=spec_file, package_version=package_version)
            )
        elif spec['dependencies'][package_name] != package_version:
            messages.append('Changing {package_name} from version {package_version} to {other_package_version}'.format(
                    package_version=package_version, package_name=package_name,
                    other_package_version=spec['dependencies'][package_name])
            )

            spec['dependencies'][package_name] = package_version

    test_deps = {}

    for (package_name, package_version) in spec['dependencies'].items():
        if package_name not in top_level['dependencies']:
            test_deps[package_name] = package_version

    if note_test_deps:
        spec['test-dependencies'] = sorted_deps(test_deps)

    if len(messages) > 0 or note_test_deps:
        print('{number} packages changed.'.format(number=len(messages)))

        if not dry:
            spec['dependencies'] = sorted_deps(spec['dependencies'])
            with open(spec_file, 'w') as f:
                json.dump(spec, f, sort_keys=False, indent=4, separators=(',', ': '))
        else:
            print("No changes written.")

        if not quiet:
            print('\n'.join(messages))
    else:
        print('No changes needed.')


def sorted_deps(deps):
    return OrderedDict(sorted(deps.items()))


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
