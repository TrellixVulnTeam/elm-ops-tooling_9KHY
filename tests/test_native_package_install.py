import json
import tarfile
import difflib
import shutil

import native_package_install


def test_main_does_not_download_twice_given_multiple_elm_packages(tmpdir, mocker):
    native_elm_package = {'elm-lang/core': '1.0.0'}
    native_elm_package_path = tmpdir.join('elm-native-package.json')
    native_elm_package_path.write(json.dumps(native_elm_package))

    fake_native_tarball_path = tmpdir.join('core.tgz')
    with tmpdir.as_cwd():
        with tarfile.open(str(fake_native_tarball_path), 'w') as f:
            fake_elm_package = tmpdir.mkdir('core-1.0.0').join('elm-package.json')
            fake_elm_package.write(json.dumps({
                'source-directories': ['src', 'src2'],
            }))
            f.add(str(fake_elm_package.relto(tmpdir)))

    elm_package_one_path = tmpdir.join('elm-package-one.json')
    elm_package_one_path.write(json.dumps({
        'repository': 'https://github.com/NoRedInk/elm-ops-tooling.git',
        'source-directories': ['.'],
        'dependencies': {},
    }))

    elm_package_two_path = tmpdir.join('elm-package-two.json')
    elm_package_two_path.write(json.dumps({
        'repository': 'https://github.com/NoRedInk/elm-ops-tooling-two.git',
        'source-directories': ['src'],
        'dependencies': {},
    }))

    vendor = tmpdir.mkdir('vendor')

    def write_tarfile(_, tar_filename):
        shutil.copyfile(str(fake_native_tarball_path), tar_filename)

    mock_urlretrieve = mocker.patch.object(
        native_package_install,
        'urlretrieve',
        side_effect=write_tarfile)

    run_install = lambda: native_package_install.main(
        str(native_elm_package_path),
        list(map(str, (elm_package_one_path, elm_package_two_path))),
        str(vendor))

    run_install()
    run_install()

    assert mock_urlretrieve.call_count == 1


def test_update_source_directories_makes_minimum_changes(tmpdir):
    vendor_dir = tmpdir.mkdir('vendor')

    elm_package_one_path = tmpdir.join('elm-package-one.json')
    elm_package_one_path.write(json.dumps({
        'repository': 'https://github.com/NoRedInk/elm-ops-tooling.git',
        'source-directories': ['.'],
        'dependencies': {},
    }, indent=4, separators=(',', ': ')))

    elm_package_two_path = tmpdir.join('elm-package-two.json')
    elm_package_two_path.write(json.dumps({
        'repository': 'https://github.com/NoRedInk/elm-ops-tooling-two.git',
        'source-directories': ['src'],
        'dependencies': {},
    }, indent=4, separators=(',', ': ')))

    native_packages = [{'owner': 'elm-lang', 'project': 'core', 'version': '1.0.0'}]
    vendor_package_dir = vendor_dir.mkdir('elm-lang').mkdir('core-1.0.0')
    fake_elm_package = vendor_package_dir.join('elm-package.json')
    fake_elm_package.write(json.dumps({
        'source-directories': ['src', 'src2'],
    }))
    src_dir = vendor_package_dir.join('src').relto(tmpdir)
    src2_dir = vendor_package_dir.join('src2').relto(tmpdir)

    prev_lines = elm_package_one_path.read().splitlines()

    # sanity check: we're operating on a clean JSON
    for line in prev_lines:
        assert not line.endswith(' ')

    repo = native_package_install.update_source_directories(
        str(vendor_dir),
        list(map(str, (elm_package_one_path, elm_package_two_path))),
        native_packages,
    )

    assert repo == 'https://github.com/NoRedInk/elm-ops-tooling-two.git'

    new_elm_package_one = json.loads(elm_package_one_path.read())
    assert set(new_elm_package_one['source-directories']) == set(('.', str(src_dir), str(src2_dir)))

    new_elm_package_two = json.loads(elm_package_two_path.read())
    assert set(new_elm_package_two['source-directories']) == set(('src', str(src_dir), str(src2_dir)))

    for diff in difflib.ndiff(prev_lines, elm_package_one_path.read().splitlines()):
        if diff.startswith('  '):
            continue

        # assert there's only expected diffs
        if diff.startswith('+ '):
            # adds new src dir or trailing comma
            assert ('"."' in diff) or (str(src_dir) in diff) or (str(src2_dir) in diff)
        elif diff.startswith('- '):
            # trailing comma for src dir
            assert '"."' in diff
        elif diff.startswith('? '):
            pass
        else:
            assert False, 'unexpected diff operator in: ' + diff
