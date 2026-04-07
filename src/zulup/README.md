# ZULUP

* Specification : [AGENTS.md](AGENTS.md)
* Reference: [README_reference.md](README_reference.md)


## User Miniguide

### Preparation

Place `run_zulup.sh` into a folder with a `zulup_backup.json` or top folders of such.

**run_zulup.sh**
```bash
#!/bin/bash
uv run --with=git+https://github.com/hmaerki/maerki_util.git@main zulup "$@"
```

Place `zulup_backup.json` and `zulup_backup.sh` in the project directory to be backed up:

**zulup_backup.json**
```json
{
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
```

### Command line

```bash
# cd into the folder containing zulup_backup.json and zulup_backup.sh
cd ~/projects/project_heizung

# Run a backup
./run_zulup.sh

# List all snapshots for this project
./run_zulup.sh snapshots .

# List files in a specific snapshot
./run_zulup.sh list /tmp/backup/project_heizung_2026-04-07_10-00-00_full.json

# Restore specific files from a snapshot (into the current directory)
./run_zulup.sh restore /tmp/backup/project_heizung_2026-04-07_10-00-00_full.json file_a.py file_b.ods
```
