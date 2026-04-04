# Programm Zulup

## Intro

Zulup is a backup software.

Terms

* `backup`: A backup will be done for a certain directory.
* `backup_name`: The name of a backup. Examples `project_xy`, `project_rs`.
* `backup_directory`: The directory to backup.
* `snapshot`: A snapshot is a tar file containing a backup. The initial snapshot is full, subsequent snapshots are incremental. A snapshot always consists of a `tarfile` and a `metafile`.
* The `snapshot_stem` is the stem of the snapshot file. It is composed as follows:
  * `<backup_name>_<snapshot_datetime>_<snapshot_type>`
  * `snapshot_datetime` is `YY-MM-DD_HH-MM-SS`
  * `snapshot_type` is `full` or `incr`.
* `tarfile`: Belongs to a snapshot. The filename is `<snapshot_stem>.zst`
* `metafile`: Belongs to a snapshot. The filename is `<snapshot_stem>.json`
* `verb`: If a file has been `added` to a backup. A `modified` version was added. Or if the file was `untouched` or `removed`.
* `directory_src`: The directory where the snapshots for this backup are stored.
* `directory_target`: The directory where the snapshots for this backup are stored.

## Backup instructions files

`zulup` start searching from the home folder for `zulup.json` files.

If a `zulup.json` file with `backup` is found: A backup is created.

## zulup.json

This file contains instructions.

* Recurse only by one directory level.

  ```json
  { "depth": 1 }
  ```

  If I directory is known to have many files/directories but non more `zulup.json`. So this instructions prevents searching the whole tree.

* Backup

  ```json
  "backup": {
    "backup_name": "project_xy",
    "directory_target": "/mnt/backup",
    "directory_src": ".",
    "directory_name_include": true,
    "select": "see below", 
  }
  ```

  `directory_src` may be a relative or absolute path.

  If `directory_src` is `.` the directory name will NOT be included.


* Include/Exclude options

  ```json
  "select": [
    {
        "pattern": "README.md",
        "tags": ["exclude", "name"],
    },
  ]
  ```

  * `pattern` for regexp
  * `text` for text
  * `tags`
    * "exclude" or "include" (default)
    * "ignorecase" or "case" (default)
    * "path" or "name" (default)

## `metafile`

```json
{
    "backup" : {
        "backup_name": "project_xy",
        "parent": "/home/maerki/Downloads",
        "hostname": "maerki-ideapad-320",
        "tar_checksum": "sha256:4efb75d..."
    },
    "current": {
        "snapshot_datetime": "2026-04-03_14-22-22",
        "snapshot_type": "incr",
        "snapshot_stem": "project_xy_2026-04-03_13-22-22_incr"
    },
    "history": [
        {
            "snapshot_datetime": "2026-04-03_12-22-22",
            "snapshot_type": "full",
            "snapshot_stem": "project_xy_2026-04-03_13-22-22_full",
            "tar_checksum": "sha256:4efb75d..."
        },
        {
            "snapshot_datetime": "2026-04-03_13-22-22",
            "snapshot_type": "incr",
            "snapshot_stem": "project_xy_2026-04-03_13-22-22_incr",
            "tar_checksum": "sha256:4efb75d..."
        }
    ],
    "files": [
        {
            "path": "Fedora-Server-netinst-x86_64-43-1.6.iso",
            "size": "1182896128",
            "modified": "2026-03-31_07-50-42.124",
            "verb": "added",
            "snapshot_datetime": "2026-04-03_12-22-22"
        },
        {
            "path": "usb_specificaton/Audio40.pdf",
            "size": "123456",
            "modified": "2026-03-31_07-50-42.124",
            "verb": "modified",
            "snapshot_datetime": "2026-04-03_13-22-22",
        }
    ]
}
```

This is the file which is stored with very snapshot.

## `zulup` backup sequence

* Loop over the directory structure and find all backups to be done based on `zulup.json`.
* For each backup:
  * Traverse `directory_src` and collect files according to `select`: We call it `current_filelist`.
  * Find the last snapshot in `directory_target`.
  * Read `metafile` from last snapshot. We call it `last_metafile`.
  * Merge `last_metafile` with `current_filelist` into `new_metafile`. In this step the `verb` will updated:
    * `added`: If the file is new.
    * `removed`: if the file is gone.
    * `untouched`: If the file size and modification time have not changed.
    * `modified`: else
  * Create a file list as input into `tar --files-from`.
  * Call `tar --zstd --files-from ... -cf <directory_target>/<snapshot_stem>.zst_tmp`.
  * Calculate sha256 from <directory_target>/<snapshot_stem>.zst and add it to `backup/tar_checksum` of `new_metafile`.
  * Store `new_metafile` in `<directory_target>/<snapshot_stem>.json`.
  * Rename `<snapshot_stem>.zst_tmp` to `<snapshot_stem>.zst`

