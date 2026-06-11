# ZULUX

zulux resets access permissions for files and directories.

## User Miniguide

### Preparation

Place `run_zulux.sh` into a folder with a `zulux_chmod.json` or top folders of such.

**run_zulux.sh**
```bash
#!/bin/bash
uv run --with=git+https://github.com/hmaerki/maerki_util.git@main zulux "$@"
```

Place `zulux_chmod.json` in the project directory:

**zulux_chmod.json**

```json
[
    {
        "directory_self": {
            "chmod": "www-data:users:rwxr-xr-x"
        },
        "files": {
            "patterns": [
                "wikiwiki/*.cgi"
            ],
            "chmod": "www-data:users:rwxrwx---"
        },
        "directories": {
            "patterns": [
                "*/"
            ],
            "chmod": "www-data:users:rwxr-xr-x"
        }
    }
]
```

Rules are evaluated from top to bottom. The first matching pattern is applied; if no rule matches, permissions are NOT changed. All members may be left out.

Patterns use `.gitignore`-style syntax:
* `*` matches everything except `/`
* A pattern starting with `!` means exclude.
* Patterns in `"directories"` MUST end with `/`.

### Filename prefix

The filename prefix before `zulux_chmod.json` determines which directory the rules apply to:

* `zulux_chmod.json` (no prefix): rules apply to the directory containing the file.
* `http_zulux_chmod.json` (prefix `http`): rules apply to the sibling directory `http/`. It is an error if that sibling directory does not exist.

### Command line

```bash
zulux <directories>
```

One or multiple directories may be provided. Each directory is traversed recursively until a `*zulux_chmod.json` is found; recursion into that directory then stops.

```bash
zulux --dry-run <directories>
```

Prints proposed changes to stdout without applying them.
