import json
import tarfile
import urllib2

import native_package_install



def test_main(tmpdir, mocker):
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
    }))

    elm_package_two_path = tmpdir.join('elm-package-two.json')
    elm_package_two_path.write(json.dumps({
        'repository': 'https://github.com/NoRedInk/elm-ops-tooling-two.git',
        'source-directories': ['src'],
    }))

    vendor = tmpdir.mkdir('vendor')

    urlopen = mocker.patch.object(urllib2, 'urlopen')
    with open(str(fake_native_tarball_path)) as f:
        urlopen.return_value = f

        native_package_install.main(
            str(native_elm_package_path),
            list(map(str, (elm_package_one_path, elm_package_two_path))),
            str(vendor))

        # mvp is to test that main runs without raising an exception;
        # not asserting anything for now
