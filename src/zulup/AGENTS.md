# Programm Zulup

## Intro

Zulup is a backup software.

The file `zulup.py` contains some starting point.

Terms

* `backup`: A backup will be done for a certain directory.
* `backup_name`: The name of a backup. Examples `project_xy`, `project_rs`.
* `snapshot`: A snapshot is a tar file containing a backup. The initial snapshot is full, subsequent snapshots are incremental. A snapshot always consists of a `tarfile` and a `metafile`.
* The `snapshot_stem` is the stem of the snapshot file. It is composed as follows:
  * `<backup_name>_<snapshot_datetime>_<snapshot_type>`
  * `snapshot_datetime` is `YYYY-MM-DD_HH-MM-SS`
  * `snapshot_type` is `full` or `incr`.
* `tarfile`: Belongs to a snapshot. The filename is `<snapshot_stem>.tgz`
* `metafile`: Belongs to a snapshot. The filename is `<snapshot_stem>.json`
* `verb`: The action that happened to a file: `added` (new file), `modified` (changed), `untouched` (unchanged), or `removed` (deleted).
* `directory_src`: The directory to be backed up.
* `directory_target`: The directory where the snapshots for this backup are stored.

## Backup instructions files

`zulup` starts searching from the home folder for `zulup.json` files.

If a `zulup.json` file with `backup` is found: A backup is created.

## zulup.json

This file contains instructions.

* Recurse only by one directory level.

  ```json
  { "depth": 1 }
  ```

  If `depth` is not specified: The whole directory will be traversed.

  If `depth` is 0. No subdirectories will be traversed.

  If `depth` is 1. Traverse one directory down.

  Rationale: If a directory is known to have many files/directories but no more `zulup.json`. So this `depth` instruction prevents searching the whole tree for more `zulup.json` files.

* Backup

  ```json
  {
    "backup": {
      "backup_name": "project_xy",
      "directory_target": "/mnt/backup",
      "directory_src": ".",
      "directory_name_include": true,
      "filters": "see below"
    }
  }
  ```

  `directory_src` may be a relative or absolute path.

  Example: `/home/maerki/project_xy/zulup.json`

  `zulup.json` has set `"directory_src": "."`.

  If `"directory_name_include": true` the added files are `project_xy/README.md`, `project_xy/image.jpg` ...

  If `"directory_name_include": false` the added files are `README.md`, `image.jpg` ...

* Include/Exclude options

  ```json
  "filters": [
    {
        "name": "README.md",
        "matching": "literal",
        "kind": "directory",
        "logic": "exclude"
    }
  ]
  ```

  * `path`/`name`: If the pattern should match the file path or just the file name.
  * `matching`: One of `literal`(default), `nocase`(for case insensitive) or `regexp`.
  * `kind`: One of `file`(default) or `directory`.
  * `logic`: One of `exclude`(default) or `include`.

  How the filters work:

  * By default the file is included.
  * Loop over all filters
    * If a filter matches:
      * `include` or `exclude` depnding on `logic`
      * terminate loop

## `metafile`

Metafile contains all files which were found at the time of the snapshot.

Only files whose `verb` is `added` or `modified` are added to the `tarfile` (incremental backup).

In the `files` array, `snapshot_datetime` records the snapshot in which the current `verb` was assigned.

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
        "snapshot_stem": "project_xy_2026-04-03_14-22-22_incr"
    },
    "history": [
        {
            "snapshot_datetime": "2026-04-03_12-22-22",
            "snapshot_type": "full",
            "snapshot_stem": "project_xy_2026-04-03_12-22-22_full",
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
            "size": 1182896128,
            "modified": "2026-03-31_07-50-42.124",
            "verb": "added",
            "snapshot_datetime": "2026-04-03_12-22-22"
        },
        {
            "path": "usb_specificaton/Audio40.pdf",
            "size": 123456,
            "modified": "2026-03-31_07-50-42.124",
            "verb": "modified",
            "snapshot_datetime": "2026-04-03_13-22-22"
        },
        {
            "path": "old_notes.txt",
            "size": 4096,
            "modified": "2026-03-20_10-00-00.000",
            "verb": "removed",
            "snapshot_datetime": "2026-04-03_14-22-22"
        }
    ]
}
```

This is the file which is stored with every snapshot.

## `zulup` backup sequence

* Loop over the directory structure and find all backups to be done based on `zulup.json`.
* For each backup:
  * Do minimal checks
    * Traverse `directory_src` and collect files according to `filters`: We call it `current_filelist`.
    * Find the last snapshot in `directory_target`. If no previous snapshot exists, this is a full backup and all files are `added`.
    * Read `metafile` from last snapshot. We call it `last_metafile`.
* For each backup:
  * Merge `last_metafile` with `current_filelist` into `new_metafile`. In this step the `verb` will be updated:
    * `added`: If the file is new.
    * `removed`: if the file is gone.
    * `untouched`: If the file size and modification time have not changed.
    * `modified`: else
  * Create a file list as input into `tar --files-from`: All files which are `added` or `modified`.
  * Call `tar --zstd --files-from ... -cf <directory_target>/<snapshot_stem>.tgz_tmp`.
  * Calculate sha256 from `<directory_target>/<snapshot_stem>.tgz_tmp` and add it to `backup/tar_checksum` of `new_metafile`.
  * Store `new_metafile` in `<directory_target>/<snapshot_stem>.json`.
  * Rename `<snapshot_stem>.tgz_tmp` to `<snapshot_stem>.tgz`

