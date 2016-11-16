#! /usr/bin/env python
'''
Load and save elm-package.json safely.
'''

# from typing import Dict, Tuple, IO
import copy
from collections import OrderedDict
import json


def load(fileobj):
    # type: (IO[str]) -> Dict
    return json.load(fileobj, object_pairs_hook=OrderedDict)


def dump(package, fileobj):
    # type: (Dict, IO[str]) -> None
    to_save = copy.deepcopy(package)
    to_save['dependencies'] = sorted_deps(to_save['dependencies'])
    json.dump(to_save, fileobj, sort_keys=False, indent=4, separators=(',', ': '))


def sorted_deps(deps):
    # type: (Dict) -> Dict
    return OrderedDict(sorted(deps.items()))


def sync_deps(from_deps, to_deps):
    # type: (Dict, Dict) -> Tuple[List[str], Dict]
    messages = []
    result = copy.deepcopy(to_deps)

    for (package_name, package_version) in from_deps.items():
        if package_name not in to_deps:
            result[package_name] = package_version

            messages.append('Inserting new package {package_name} at version {package_version}'.format(
                package_name=package_name, package_version=package_version)
            )
        elif to_deps[package_name] != package_version:
            result[package_name] = package_version

            messages.append('Changing {package_name} from version {package_version} to {other_package_version}'.format(
                package_version=package_version, package_name=package_name,
                other_package_version=to_deps[package_name])
            )

    return messages, result
