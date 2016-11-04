from collections import OrderedDict
import json

import pytest
from hypothesis import given
import hypothesis.strategies as st

import elm_deps_sync


package_skeleton = {
    "version": "1.0.0",
    "summary": "test elm deps sync",
    "repository": "https://github.com/NoRedInk/elm-ops-tooling",
    "license": "BSD-3",
    "source-directories": ".",
    "exposed-modules": [],
    "native-modules": True,
    "dependencies": {},
    "elm-version": "0.17.0 <= v <= 0.17.0",
}

top_level_deps = [
    ('NoRedInk/top-1', '1.0.0 <= v <= 1.0.0'),
    ('NoRedInk/top-2', '1.0.0 <= v <= 1.0.0'),
    ('NoRedInk/top-3', '1.0.0 <= v <= 1.0.0'),
]

spec_deps = [
    ('NoRedInk/top-1', '1.0.0 <= v <= 1.0.0'),
    ('NoRedInk/top-2', '1.0.0 <= v <= 1.0.0'),
    ('NoRedInk/spec-1', '1.0.0 <= v <= 1.0.0'),
    ('NoRedInk/spec-2', '1.0.0 <= v <= 1.0.0'),
]


@given(top_level_keys=st.permutations(package_skeleton.keys()),
       top_level_deps=st.permutations(top_level_deps),
       spec_keys=st.permutations(package_skeleton.keys()),
       spec_deps=st.permutations(spec_deps))
def test_spec_order_is_preserved(
        tmpdir,
        top_level_keys,
        top_level_deps,
        spec_keys,
        spec_deps):
    top_level_file = tmpdir.join('elm-package.json')
    spec_file = tmpdir.join('spec-elm-package.json')

    top_level = _make_package(top_level_keys, top_level_deps)
    top_level_file.write(json.dumps(top_level))

    spec = _make_package(spec_keys, spec_deps)
    spec_file.write(json.dumps(spec))

    elm_deps_sync.sync_versions(
        str(top_level_file),
        str(spec_file),
        quiet=False,
        dry=False,
        note_test_deps=True)

    new_spec = json.loads(spec_file.read(), object_pairs_hook=OrderedDict)
    assert new_spec.keys() == spec_keys + ['test-dependencies']
    assert new_spec['dependencies'].keys() == ['NoRedInk/spec-1', 'NoRedInk/spec-2', 'NoRedInk/top-1', 'NoRedInk/top-2', 'NoRedInk/top-3']
    assert new_spec['test-dependencies'].keys() == ['NoRedInk/spec-1', 'NoRedInk/spec-2']


def _make_package(keys, deps):
    package = OrderedDict((key, package_skeleton[key]) for key in keys)
    package['dependencies'] = OrderedDict(deps)
    return package
