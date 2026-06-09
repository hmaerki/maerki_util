# Program ZULUX

## Intro

zulux resets access permissions for files and directories.

## `zulux` instruction files

`zulux` scans the directory tree for these configuration files:

* `*zulux_chmod.json`: Defines how to set permissions for that directory.

  The filename must end with `zulux_chmod.json`. The prefix can be anything (e.g. `zulux_chmod.json`, `A_zulux_chmod.json`, `mysite_zulux_chmod.json`).


## *zulux_chmod.json

See: [zulux_chmod.json](src/zulux/examples/ergoinfo_ch/zulux_chmod.json)

Behavior:

* zulux scans all files and directories in the directory that contains `*zulux_chmod.json`.
* For each file and directory, entries in `*zulux_chmod.json` are evaluated from top to bottom.
  * As soon as a matching entry is found, it is applied.
    * Example file: `wikiwiki/x/run.cgi`
    * Applied value: `"chmod": "www-data:users:rwxrwx---"`
    * Processing for this file then stops.
  * If none of the rules apply, permissions are NOT changed.

`"directory_self"`: Refers to the directory where `*zulux_chmod.json` is located. It has exactly one subelement: `"chmod"`.

`"files"` and `"directories"` are handled in the same way, for files and directories respectively.

Patterns in `"files"` must NOT end with `/`; patterns in `"directories"` MUST end with `/`.

* Selection rules (single patterns list)

  ```json
  "patterns": [
    "*.pyc",
    "!important.txt"
  ]
  ```

  Patterns use `.gitignore`-style syntax based on Python's `fnmatch` module.

  Pattern syntax:
  * `*` matches everything except `/`
  * `?` matches any single character except `/`
  * `[seq]` matches any character in *seq*

  Rules:
  * Patterns are evaluated from top to bottom. The first matching pattern decides.
  * A pattern starting with `!` means exclude.
  * A pattern without `!` means include.
  * By default, no files or directories are selected.
  * A pattern containing `/` (other than a trailing `/`) is matched against the relative path. Otherwise, it is matched against the file or directory name only.
  * If `"patterns"` is missing, an empty list is assumed.

  Examples:
  * `"*.log"` - include all `.log` files.
  * `"!private.log"` - exclude `private.log`.
  * `".git/"` - include every directory named `.git` (top folder and all subfolders).
  * `"!build/output/"` - exclude the `output` directory under `build` (path match).

  Order matters example: to include all `.cgi` files under `wikiwiki/` except `secret.cgi`:
  ```json
  "patterns": [
    "!wikiwiki/secret.cgi",
    "wikiwiki/*.cgi"
  ]
  ```
  `secret.cgi` matches the first pattern (`!` = exclude) and is rejected immediately; all other `.cgi` files fall through to the second pattern and are included.

### Difference between `zulux_chmod.json` and `http_zulux_chmod.json`

The prefix before `zulux_chmod.json` determines which directory the rules are applied to:

* `zulux_chmod.json` (no prefix):

  Rules are applied to the directory that contains the file itself.

* `http_zulux_chmod.json` (prefix `http`):

  The prefix must match the name of a sibling directory located next to the file.
  Rules are applied to that sibling directory (`http/`) as if the file were placed inside it.
  It is an error if the sibling directory does not exist.

### `"chmod": "www-data:users:rwxr-xr-x"`:

* `www-data` is the user name to apply.
* `users` is the group name to apply.
* `rwxr-xr-x` is the permissions string to apply.

If one of the above fields is empty, it is not applied.

This value is mandatory and must contain exactly 2 `:` characters.

## zulux command line syntax

```bash
zulux <directories>
```

One or multiple directories may be provided. Each directory is traversed recursively until a `*zulux_chmod.json` is found; recursion into that directory then stops.
After discovery, all found `*zulux_chmod.json` files are applied.


## Implementation

* Naming of variables/properties for filenames
  * good: filename_xy
  * bad: path_xy

* Naming of variables/properties for directories
  * good: directory_xy
  * bad: path_xy

* Always use ISO units in the variable/property name. Always singular.
  * good: duration_s
  * bad: started_at

## Source directory

* `src/zulux`: Implementation of zulux.

## Test directory

* `tests/zulux`: Tests for zulux

Test strategy:

  A test should be structured as follows:
  * test_a_zulux_chmod.json
  * test_a_input.txt
  * test_a_expected.txt

  `test_a_input.txt` contains a list of one file or directory per line.

  Now `test_a_zulux_chmod.json` is applied and the result written in `test_a_expected.txt` using this format:

  `<applied user : applied group : applied mode> <filename>`

  As `test_a_expected.txt` is committed to git and then overwritten by the test - if the file changes/the test fails, it will be marked as a change.
  Use a git command in the test to verify if the file differs:
  ```
  git diff --quiet path/to/file
  Exit code 0 → no changes
  Exit code 1 → file has changes
  ```
