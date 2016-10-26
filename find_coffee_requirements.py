#! /usr/bin/env python
from __future__ import print_function

import argparse
import re

# = require blah
#= require blah
#= require "blah"
#=require blah
require_regex = re.compile("#[ ]*=[ ]*require[ \"']*(.+?)[\"'\s]+")


def get_require_lines(filename):
    require_lines = []

    with open(filename) as f:
        for line in f:
            matches = re.match(require_regex, line)

            if matches is not None:
                require = matches.groups()[0]
                require_lines.append(require)
    return require_lines


# get_requirement_filenames(starting_filename: str) -> Tuple[List[str], List[str]]
def get_requirement_filenames(assets_dir, starting_filename):
    all_file_names = []
    missing_file_names = []

    require_lines = get_require_lines(starting_filename)

    for require in require_lines:
        try:
            current_require_lines, current_missing_filenames = get_requirement_filenames(
                assets_dir,
                "{assets_dir}{require}.js.coffee".format(
                    assets_dir=assets_dir,
                    require=require
                )
            )
            all_file_names.extend(current_require_lines)
            missing_file_names.extend(current_missing_filenames)
        except IOError:
            missing_file_names.append(require)
            continue

    all_file_names.extend(
        require for require in require_lines
        if require not in missing_file_names
    )

    return (list(set(all_file_names)), list(set(missing_file_names)))



def main():
    parser = argparse.ArgumentParser(description='Check deps matching between a parent and a sub')

    # example 'app/assets/javascripts/teach/course-creation-component.js.coffee'
    parser.add_argument('filename', help='The file to use for starting the requirement search')
    parser.add_argument('--asset-dir', dest='asset_dir', const='./', default='./', action='store', nargs='?', help='Asset dir to look into')
    args = parser.parse_args()

    (requirement_filenames, missing_filenames) = get_requirement_filenames(args.asset_dir, args.filename)

    print('\n'.join(requirement_filenames))
    print('--------------\n But I couldn\'t find the following files:\n\n')
    print('\n'.join(missing_filenames))


if __name__ == '__main__':
    main()
