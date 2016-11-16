#! /usr/bin/env python

from __future__ import print_function

import argparse
import collections
import fnmatch
import json
import os
import sys
import tarfile
import urllib2


def read_native_elm_package(package_file):
    """
    Reads elm-native-package.json.
    """

    with open(package_file) as f:
        return json.load(f)


def format_tarball_url(package):
    """
    Creates the url to fetch the tar from github.
    >>> format_tarball_url({'user': 'elm-lang', 'project': 'navigation', 'version': '2.0.0'})
    'https://github.com/elm-lang/navigation/archive/2.0.0.tar.gz'
    """
    return "https://github.com/{user}/{project}/archive/{version}.tar.gz".format(**package)


def packages_from_exact_deps(exact_dependencies):
    """
    Parses the json and returns a list of {version, user, project}.
    >>> packages_from_exact_deps({'elm-lang/navigation': '2.0.0'})
    [{'version': '2.0.0', 'user': 'elm-lang', 'project': 'navigation'}]
    """
    result = []

    for package, version in exact_dependencies.items():
        user, project = package.split('/')
        result.append({
          'user': user,
          'project': project,
          'version': version
        })

    return result


def ensure_vendor_user_dir(base, user):
    """
    Creates the path in the vendor folder.
    >>> ensure_vendor_user_dir('foo', 'bar')
    'foo/bar'
    """
    path = os.path.join(base, user)

    try:
        os.makedirs(path)
    except Exception as e:
        pass

    return path


def vendor_package_dir(vendor_dir, package):
    """
    Returns the path to the elm package. Also creates the parent directory if misisng.
    >>> vendor_package_dir('vendor/assets/elm', {'version': '2.0.0', 'user': 'elm-lang', 'project': 'navigation'})
    'vendor/assets/elm/elm-lang/navigation-2.0.0'
    """
    vendor_user_dir = ensure_vendor_user_dir(vendor_dir, package['user'])
    return "{vendor_user_dir}/{project}-{version}".format(
        vendor_user_dir=vendor_user_dir,
        project=package['project'],
        version=package['version']
    )


def fetch_packages(vendor_dir, packages):
    """
    Fetches all packages from github.
    """
    for package in packages:
        tar_filename = format_tar_path(vendor_dir, package)
        vendor_user_dir = ensure_vendor_user_dir(vendor_dir, package['user'])
        url = format_tarball_url(package)

        print("Downloading {user}/{project} {version}".format(**package))
        tar_file = urllib2.urlopen(url)
        with open(tar_filename, 'w') as tar:
            tar.write(tar_file.read())

        with tarfile.open(tar_filename) as tar:
            tar.extractall(vendor_user_dir, members=tar.getmembers())

    return packages


def format_tar_path(vendor_dir, package):
    """
    The path of the tar.
    >>> format_tar_path('vendor/assets/elm', {'user': 'elm-lang', 'project': 'navigation', 'version': '2.0.0'})
    'vendor/assets/elm/elm-lang/navigation-2.0.0-tar.gz'
    """
    ensure_vendor_user_dir(vendor_dir, package['user'])
    return vendor_package_dir(vendor_dir, package) + "-tar.gz"


def format_native_name(user, project):
    """
    Formates the package to the user used in elm native.
    >>> format_native_name('elm-lang', 'navigation')
    '_elm_lang$navigation'
    """

    underscored_user = user.replace("-", "_")
    underscored_project = project.replace("-", "_")
    return "_{owner}${repo}".format(owner=underscored_user, repo=underscored_project)


def package_name_from_repo(repository):
    """
    User and project from repository.
    >>> package_name_from_repo('https://github.com/NoRedInk/noredink.git')
    ['NoRedInk', 'noredink']
    """

    repo_without_domain = repository.split('https://github.com/')[1].split('.git')[0]

    (user, project) = repo_without_domain.split('/')
    return (user, project)


def get_source_dirs(vendor_dir, package):
    """ get the source-directories out of an elm-package file """
    elm_package_filename = os.path.join(vendor_package_dir(vendor_dir, package), 'elm-package.json')
    with open(elm_package_filename) as f:
        data = json.load(f)

    return data['source-directories']


def replace_in_file(filePath, src, target):
    """ find replace in a file """
    output = ""
    with open(filePath) as infile:
        output = infile.read().replace(src, target)
    with open(filePath, 'w') as outfile:
        outfile.write(output)


def find_all_native_files(path):
    """ recursivly find all js files in a package """
    native_files = []
    for root, dirnames, filenames in os.walk(path):
        if "Native" not in root:
            continue
        for filename in fnmatch.filter(filenames, '*.js'):
            native_files.append(os.path.join(root, filename))
    return native_files


def munge_names(vendor_dir, repository, packages):
    """
    Replaces the namespaced function names in all native code by the namespace from the given elm-package.json.
    """
    user, project = package_name_from_repo(repository)
    for package in packages:
        native_files = find_all_native_files(vendor_package_dir(vendor_dir, package))
        for native_file in native_files:
            replace_in_file(
                native_file,
                format_native_name(package['user'], package['project']),
                format_native_name(user, project)
            )


def update_elm_package(vendor_dir, configs, packages):
    """
    Gets the repo name and updates the source-directories in the given elm-package.json.
    """

    repository = ""

    for config in configs:
        with open(config) as f:
            data = json.load(f, object_pairs_hook=collections.OrderedDict)

        repository = data['repository']
        source_directories = data['source-directories']
        path = '../' * config.count('/')

        needs_save = False

        for package in packages:
            current_package_dirs = get_source_dirs(vendor_dir, package)

            for dir_name in current_package_dirs:
                relative_path = os.path.join(path, vendor_package_dir(vendor_dir, package), dir_name)

                if relative_path not in data['source-directories']:
                    data['source-directories'].append(relative_path)
                    needs_save = True

        if needs_save:
            with open(config, 'w') as f:
                f.write(json.dumps(data, indent=4))

    return repository


def exclude_downloaded_packages(vendor_dir, packages):
  return [x for x in packages if not os.path.isfile(format_tar_path(vendor_dir, x))]


def main(native_elm_package, configs, vendor_dir):
    raw_json = read_native_elm_package(native_elm_package)
    all_packages = packages_from_exact_deps(raw_json)
    required_packages = exclude_downloaded_packages(vendor_dir, all_packages)
    fetch_packages(vendor_dir, required_packages)
    repository = update_elm_package(vendor_dir, configs, required_packages)
    munge_names(vendor_dir, repository, required_packages)


def test():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch elm packages')
    parser.add_argument(
        'native_elm_package',
        help='The elm-native-package.json file you want to use',
        default='elm-native-package.json'
    )
    parser.add_argument('--elm-config', '-e', nargs='+')
    parser.add_argument('--vendor-dir', default='vendor/assets/elm')
    parser.add_argument('--test', '-t', action='store_true')

    args = parser.parse_args()
    if args.test:
        test()
        exit()

    main(args.native_elm_package, args.elm_config, args.vendor_dir)
