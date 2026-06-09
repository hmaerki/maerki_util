# ZULUX

zulux allows to reset access permissions for files and directories.

## User Miniguide

### Preparation

Place `run_zulup.sh` into a folder with a `zulux_chmod.jsonn` or top folders of such.

**run_zulup.sh**
```bash
#!/bin/bash
uv run --with=git+https://github.com/hmaerki/maerki_util.git@main zulux "$@"
```

Place `zulux_chmod.json` and `zulup_backup.sh` in the project directory to be backed up:

**zulup_chmod.json**

```json
[
    {
        "directory_self": {
            "chmod": "www-data:users:rwxr-xr-x"
        },
        "files": {
            "include": [
                "wikiwiki/*.cgi"
            ],
            "exclude": [],
            "chmod": "www-data:users:rwxrwx---"
        },
        "directories": {
            "include": [
                "*"
            ],
            "exclude": [],
            "chmod": "www-data:users:rwxr-xr-x"
        }
    }
]
```

All members may be left out. The defaults will be used instead.

Defaults may be placed in the home directory:
**zulup_backup.json**
```json
{
}
```


### Command line

```bash
...
```
