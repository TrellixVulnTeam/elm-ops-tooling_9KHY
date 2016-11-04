from collections import OrderedDict
import json

import pytest

import elm_deps_sync


def test_spec_order_is_preserved(tmpdir):
    top_level_file = tmpdir.join('elm-package.json')
    spec_file = tmpdir.join('spec-elm-package.json')

    top_level = {
        'dependencies': OrderedDict([
            ('NoRedInk/top-3', '1.0.0 <= v <= 1.0.0'),
            ('NoRedInk/top-1', '1.0.0 <= v <= 1.0.0'),
            ('NoRedInk/top-2', '1.0.0 <= v <= 1.0.0'),
        ])
    }
    top_level_file.write(json.dumps(top_level))

    spec = {
        'dependencies': OrderedDict([
            ('NoRedInk/top-2', '1.0.0 <= v <= 1.0.0'),
            ('NoRedInk/top-1', '1.0.0 <= v <= 1.0.0'),
        ])
    }
    spec_file.write(json.dumps(spec))

    elm_deps_sync.sync_versions(
        str(top_level_file),
        str(spec_file),
        quiet=False,
        dry=False,
        note_test_deps=True)

    new_spec = json.loads(spec_file.read(), object_pairs_hook=OrderedDict)
    assert new_spec['dependencies'].keys() == ['NoRedInk/top-1', 'NoRedInk/top-2', 'NoRedInk/top-3']
