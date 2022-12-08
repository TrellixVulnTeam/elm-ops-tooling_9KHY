#! /usr/bin/env python

from __future__ import print_function

import argparse
import collections
import fnmatch
import os
import sys
import tarfile
try:
    # For Python 3.0 and later
    from urllib.request import urlretrieve
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib import urlretrieve

import elm_package
import exact_dependencies


def read_native_elm_package(package_file):
    """
    Reads elm-native-package.json.
    """

    with open(package_file) as f:
        return exact_dependencies.load(f)


def format_tarball_url(package):
    """
    Creates the url to fetch the tar from github.
    >>> format_tarball_url({'owner': 'elm-lang', 'project': 'navigation', 'version': '2.0.0'})
    'https://github.com/elm-lang/navigation/archive/2.0.0.tar.gz'
    """
    return "https://github.com/{owner}/{project}/archive/{version}.tar.gz".format(**package)


def packages_from_exact_deps(exact_dependencies):
    """
    Parses the json and returns a list of {version, owner, project}.
    >>> packages_from_exact_deps({'elm-lang/navigation': '2.0.0'}) \
        == [{'version': '2.0.0', 'owner': 'elm-lang', 'project': 'navigation'}]
    True
    """
    result = []

    for package, version in exact_dependencies.items():
        owner, project = package.split('/')
        result.append({
          'owner': owner,
          'project': project,
          'version': version
        })

    return result


def ensure_vendor_owner_dir(base, owner):
    """
    Creates the path in the vendor folder.
    >>> ensure_vendor_owner_dir('foo', 'bar')
    'foo/bar'
    """
    path = os.path.join(base, owner)

    try:
        os.makedirs(path)
    except Exception as e:
        pass

    return path


def vendor_package_dir(vendor_dir, package):
    """
    Returns the path to the elm package. Also creates the parent directory if misisng.
    >>> vendor_package_dir('vendor/assets/elm', {'version': '2.0.0', 'owner': 'elm-lang', 'project': 'navigation'})
    'vendor/assets/elm/elm-lang/navigation-2.0.0'
    """
    vendor_owner_dir = ensure_vendor_owner_dir(vendor_dir, package['owner'])
    return "{vendor_owner_dir}/{project}-{version}".format(
        vendor_owner_dir=vendor_owner_dir,
        project=package['project'],
        version=package['version']
    )


def fetch_packages(vendor_dir, packages):
    """
    Fetches all packages from github.
    """
    for package in packages:
        tar_filename = format_tar_path(vendor_dir, package)
        vendor_owner_dir = ensure_vendor_owner_dir(vendor_dir, package['owner'])
        url = format_tarball_url(package)

        print("Downloading {owner}/{project} {version}".format(**package))
        urlretrieve(url, tar_filename)
        with tarfile.open(tar_filename) as tar:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, vendor_owner_dir, members=tar.getmembers())

    return packages


def format_tar_path(vendor_dir, package):
    """
    The path of the tar.
    >>> format_tar_path('vendor/assets/elm', {'owner': 'elm-lang', 'project': 'navigation', 'version': '2.0.0'})
    'vendor/assets/elm/elm-lang/navigation-2.0.0-tar.gz'
    """
    ensure_vendor_owner_dir(vendor_dir, package['owner'])
    return vendor_package_dir(vendor_dir, package) + "-tar.gz"


def format_native_name(owner, project):
    """
    Formates the package to the owner used in elm native.
    >>> format_native_name('elm-lang', 'navigation')
    '_elm_lang$navigation'
    """

    underscored_owner = owner.replace("-", "_")
    underscored_project = project.replace("-", "_")
    return "_{owner}${repo}".format(owner=underscored_owner, repo=underscored_project)


def package_name_from_repo(repository):
    """
    Owner and project from repository.
    >>> package_name_from_repo('https://github.com/NoRedInk/noredink.git')
    ('NoRedInk', 'noredink')
    """

    repo_without_domain = repository.split('https://github.com/')[1].split('.git')[0]

    (owner, project) = repo_without_domain.split('/')
    return (owner, project)


def get_source_dirs(vendor_dir, package):
    """ get the source-directories out of an elm-package file """
    elm_package_filename = os.path.join(vendor_package_dir(vendor_dir, package), 'elm-package.json')
    with open(elm_package_filename) as f:
        data = elm_package.load(f)

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
    owner, project = package_name_from_repo(repository)
    for package in packages:
        native_files = find_all_native_files(vendor_package_dir(vendor_dir, package))
        for native_file in native_files:
            replace_in_file(
                native_file,
                format_native_name(package['owner'], package['project']),
                format_native_name(owner, project)
            )


def update_source_directories(vendor_dir, elm_package_paths, native_packages):
    """
    Updates the source-directories in the given elm-package.json files.
    Returns the repository of the last elm-package.json.
    """

    repository = ""

    for elm_package_path in elm_package_paths:
        with open(elm_package_path) as f:
            data = elm_package.load(f)

        repository = data['repository']
        source_directories = data['source-directories']
        elm_package_dir = os.path.dirname(elm_package_path)

        needs_save = False

        for native_package in native_packages:
            source_dirs = get_source_dirs(vendor_dir, native_package)

            for source_dir in source_dirs:
                absolute_source_dir = os.path.join(
                    vendor_package_dir(vendor_dir, native_package), source_dir)
                relative_path = os.path.relpath(absolute_source_dir, elm_package_dir)

                if relative_path not in data['source-directories']:
                    data['source-directories'].append(relative_path)
                    needs_save = True

        if needs_save:
            with open(elm_package_path, 'w') as f:
                elm_package.dump(data, f)

    return repository


def exclude_existing_packages(vendor_dir, packages):
  return [x for x in packages if not package_exists(vendor_dir, x)]


def package_exists(vendor_dir, package):
    return os.path.isdir(vendor_package_dir(vendor_dir, package))


def main(native_elm_package_path, elm_package_paths, vendor_dir):
    absolute_vendor_dir = os.path.abspath(vendor_dir)
    absolute_elm_package_paths = list(map(os.path.abspath, elm_package_paths))

    raw_json = read_native_elm_package(native_elm_package_path)
    all_packages = packages_from_exact_deps(raw_json)
    required_packages = exclude_existing_packages(absolute_vendor_dir, all_packages)
    fetch_packages(absolute_vendor_dir, required_packages)
    repository = update_source_directories(
        absolute_vendor_dir, absolute_elm_package_paths, required_packages)
    munge_names(absolute_vendor_dir, repository, required_packages)


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
