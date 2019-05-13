# elm-ops-tooling
Tooling for Elm ops

## update_elm_package

Automate upgrading to 0.17! Automate your elm-package and your file upgrades.

It will:

- tell you if any of your deps haven't been updated for 0.17 yet
- update module exposing syntax
- update the packages to the 0.17 version
- run elm-package install and elm-make to make sure it worked
- replace packages if they have been renamed (evancz/elm-html to elm-lang/html for example)

## update_018_elm_package

Automate upgrading to 0.18! Automate your elm-package and your file upgrades.

It will:

- tell you if any of your deps haven't been updated for 0.18 yet
- update syntax using elm-format
- update the packages to the 0.18 version
- run elm-package install and elm-make to make sure it worked
- replace packages if they have been renamed (evancz/elm-http to elm-lang/http for example)

```
python update_018_elm_package.py ../upgrades/elm-lazy-list
```

will upgrade the package in that directory.

## elm_deps_check

Sometimes we need to make sure that two different exact-dependencies are the same. This is the case when you have a parent project, and a test project where the parent project dependencies are a sub list of test project.

Usage:

- `--exact` flag if you are passing `exact-dependencies.json`
- `--quiet` flag if you only want the error message

```bash

python elm_deps_check.py elm-stuff/exact-dependencies.json tests/elm-stuff/exact-dependencies.json --exact

```

will output

```bash
BUILD FAILED due to elm-deps mismatch, errors:
Package version mismatch for circuithub/elm-list-extra!

../NoRedInk/elm-stuff/exact-dependencies.json had 3.10.0
../NoRedInk/spec/elm/elm-stuff/exact-dependencies.json had 3.7.1
```

or

```bash
python elm_deps_check.py ../NoRedInk/elm-package.json ../NoRedInk/spec/elm/elm-package.json --quiet
```

## elm_deps_upgrade

Sometimes we want to figure out if our elm-package.json contains old deps.

Usage:

- `--elm-version` if you want to specify a different version of Elm. Defaults to 0.18

```bash

python elm_deps_upgrade.py elm-package.json

```

will print

```
Minors available for elm-lang/core: [2.1.0]
Majors available for elm-lang/core: [3.0.0]
Majors available for evancz/elm-html: [4.0.2, 4.0.1, 4.0.0]

```

## elm_deps_sync

Sometimes we want to sync the deps between two files, such that all the deps in one file are matched in another file.
The deps in the first file will be added to the deps in the second file. Note that this is additive.

Usage:

- `--dry` will only print the changes to happen, not write them to file
- `--quiet` will only print the final statement
- `--note` will add a `test-dependencies` field to the second file. Useful for tooling

```bash
python elm_deps_sync.py elm-package.json spec/elm/elm-package.json
```

will print

```
1 packages changed.
Package mgold/elm-date-format inserted to spec/elm/elm-package.json for the first time at version "1.1.2 <= v < 2.0.0"
```

## with_retry

Sometimes, elm-package flakes out due to connection issues. The simplest solution to this is to wrap the `elm-package install` step with our `with_retry` script, which will rerun 10 times until it succeeds, otherwise fail the build

```
with_retry.rb elm-package install
```

## elm_self_publish

Sometimes, we want to "install" our packages locally to test them before publishing them remotely. This is designed only with the use case of testing packaged, not using them in production. It doesn't provide any of the guarantees nor support that elm-package does. If you're doing production stuff, elm-package is what you want.

```
python elm_self_publish.py ../elm-css ../json-to-elm/
```

will publish elm-css into json-to-elm

## Upgrading a Python dependency

If you have Nix, you can load a shell with the necessary dependencies like this:

```
nix-shell -p python37Packages.pip-tools
```

Once in the shell, run:

```
pip-compile --upgrade-package my-package
```
