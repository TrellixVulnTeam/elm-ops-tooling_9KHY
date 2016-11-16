from collections import OrderedDict
import json

from hypothesis import given
import hypothesis.strategies as st

import native_deps_sync


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


@given(top_level_deps=st.permutations(top_level_deps),
       spec_deps=st.permutations(spec_deps))
def test_spec_order_is_preserved(
        tmpdir,
        top_level_deps,
        spec_deps):
    top_level_file = tmpdir.join('elm-native-package.json')
    spec_file = tmpdir.join('spec-elm-native-package.json')

    top_level = OrderedDict(top_level_deps)
    top_level_file.write(json.dumps(top_level))

    spec = OrderedDict(spec_deps)
    spec_file.write(json.dumps(spec))

    native_deps_sync.sync_versions(
        str(top_level_file),
        str(spec_file),
        quiet=False,
        dry=False)

    new_spec = json.loads(spec_file.read(), object_pairs_hook=OrderedDict)
    assert list(new_spec.keys()) == ['NoRedInk/spec-1', 'NoRedInk/spec-2', 'NoRedInk/top-1', 'NoRedInk/top-2', 'NoRedInk/top-3']
