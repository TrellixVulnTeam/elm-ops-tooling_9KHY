#! /usr/bin/env python
from __future__ import print_function

import sys
import json
import argparse
import textwrap


def nice_format(tmpl, *args, **kwargs):
    unwrapped = textwrap.dedent(tmpl).format(*args, **kwargs)

    paragraphs = [
        '\n'.join(textwrap.wrap(paragraph))
        for paragraph
        in unwrapped.split('\n\n')
    ]

    return '\n\n'.join(paragraphs)


class PackageNotFound(object):
    friendly = textwrap.dedent('''\
    Package {package_name} was a dependency in the reference package file
    ({reference_name}) but was not in the candidate package file
    ({candidate_name}).

    You can probably fix this error by adding {package_name} to the
    dependencies in {candidate_name}.\
    ''')

    def __init__(self, package_name, reference_name, candidate_name):
        self.package_name = package_name
        self.reference_name = reference_name
        self.candidate_name = candidate_name

    def __str__(self):
        return nice_format(
            self.friendly,
            package_name=self.package_name,
            reference_name=self.reference_name,
            candidate_name=self.candidate_name,
        )


class VersionMismatch(object):
    friendly = textwrap.dedent('''\
    Package version mismatch for {package_name}!

    The reference package file ({reference_name}) has version
    "{reference_version}", but the candidate package file ({candidate_name})
    has version "{candidate_version}".

    You can probably fix this error by changing the version bounds for
    {package_name} in {candidate_name} to "{reference_version}".\
    ''')

    def __init__(
            self,
            package_name,
            reference_name, reference_version,
            candidate_name, candidate_version):
        self.package_name = package_name
        self.reference_name = reference_name
        self.reference_version = reference_version
        self.candidate_name = candidate_name
        self.candidate_version = candidate_version

    def __str__(self):
        return nice_format(
            self.friendly,
            package_name=self.package_name,
            reference_name=self.reference_name,
            reference_version=self.reference_version,
            candidate_name=self.candidate_name,
            candidate_version=self.candidate_version,
        )


def have_matching_versions(reference_file, candidate_file, is_exact=False, quiet=True):
    """ first file should be the top level elm-package.json
        second file should be the spec file elm-package.json
    """
    reference = json.load(reference_file)
    candidate = json.load(candidate_file)

    if not is_exact:
        reference = reference['dependencies']
        candidate = candidate['dependencies']

    if not quiet:
        print(
            reference_file.name,
            json.dumps(reference, sort_keys=True, indent=4),
        )
        print(
            candidate_file.name,
            json.dumps(candidate, sort_keys=True, indent=4),
        )

    errors = []

    for (package_name, package_version) in reference.items():
        if package_name not in candidate:
            errors.append(PackageNotFound(
                package_name=package_name,
                reference_name=reference_file.name,
                candidate_name=candidate_file.name,
            ))

        elif candidate[package_name] != package_version:
            errors.append(VersionMismatch(
                package_name=package_name,
                reference_name=reference_file.name,
                reference_version=package_version,
                candidate_name=candidate_file.name,
                candidate_version=candidate[package_name],
            ))

    if len(errors) > 0:
        print('BUILD FAILED due to elm-deps mismatch, errors:')
        print('\n---\n')
        print('\n\n---\n\n'.join(str(error) for error in errors))
        return False
    else:
        if not quiet:
            print('Matching deps!')
        return True


def main():
    parser = argparse.ArgumentParser(
        description='check that deps match between two elm-package.json files.'
    )

    # arguments
    parser.add_argument(
        'reference_file', type=open,
        help='the source of truth for dependency comparisons',
    )
    parser.add_argument(
        'candidate_file', type=open,
        help='the file which should change if different from the reference',
    )

    # options
    parser.add_argument('--quiet', '-q', action='store_true', help='succeed quietly instead of printing the dependencies as they are examined', default=False)

    # deprecated options
    parser.add_argument('--exact', '-e', action='store_true', help='(DEPRECATED) these files are exact dependencies', default=False)

    args = parser.parse_args()

    if args.exact:
        print("WARNING: --exact is deprecated and will be removed in a future version.")
        print("compare your elm-package.json files directly!")

    if not have_matching_versions(args.reference_file, args.candidate_file, quiet=args.quiet, is_exact=args.exact):
        sys.exit(1)


if __name__ == '__main__':
    main()
