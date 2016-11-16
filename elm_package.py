#! /usr/bin/env python
'''
Load and save elm-package.json safely.
'''

import copy
from collections import OrderedDict
import json


# load(fileobj: Filelike) -> Dict
def load(fileobj):
    return json.load(fileobj, object_pairs_hook=OrderedDict)


# dump(package: Dict, fileobj: FileLike) -> None
def dump(package, fileobj):
    to_save = copy.deepcopy(package)
    to_save['dependencies'] = sorted_deps(to_save['dependencies'])
    json.dump(to_save, fileobj, sort_keys=False, indent=4, separators=(',', ': '))


# sorted_deps(deps: Dict) -> Dict
def sorted_deps(deps):
    return OrderedDict(sorted(deps.items()))


# Change = str
# sync_deps(from_deps: Dict, to_deps: Dict) -> (List[Change], Dict)
def sync_deps(from_deps, to_deps):
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
