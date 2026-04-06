# ZULUP


## Useful commands

```bash
time tar xf /home/maerki/tmp_backup.tgz --occurrence=1 zulup_filelist.txt

real    0m0.028s
```


Profile
```bash
.venv/bin/python -m cProfile -s cumulative -m zulup.zulup ~/work_antenna 2>&1 | head -40
```


## User Miniguide

run_zulu.sh

```bash
uv run --with=git+https://github.com/hmaerki/maerki_util.git@zulup zulup "$@"
```

zulup.json

```json
{
    "backup": {
        "backup_name": "project_heizung",
        "directory_target": "/tmp/backup",
        "directory_src": ".",
        "directory_name_include": true,
        "ignore": [
            "!*.py",
            "!*.ods",
            ".git/",
            ".venv/",
            "*"
        ]
    }
}
```
