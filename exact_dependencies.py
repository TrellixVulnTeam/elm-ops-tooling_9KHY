#! /usr/bin/env python
'''
Load and save exact-dependencies.json safely.

The format of exact-dependencies is simply a dictionary of
package name and its exact version:

    {
        "elm-lang/core": "4.0.5"
    }
'''

import json

import elm_package


load = elm_package.load


# dump(package: Dict, fileobj: FileLike) -> None
def dump(package, fileobj):
    to_save = elm_package.sorted_deps(package)
    json.dump(to_save, fileobj, sort_keys=False, indent=4, separators=(',', ': '))
