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
* `logfilefile`: Belongs to a snapshot. The filename is `<snapshot_stem>.log`
* `verb`: The action that happened to a file: `added` (new file), `modified` (changed), `untouched` (unchanged), or `removed` (deleted).
* `directory_src`: The directory to be backed up.
* `directory_target`: The directory where the snapshots for this backup are stored.

## `zulup` instruction files

`zulup` scans the directory tree for these configuration files:

* `zulup_backup.json`: Defines one backup job.
* `zulup_backup_defaults.json`: Optional global defaults (same schema as `zulup_backup.json`) loaded from `~/zulup_backup_defaults.json`; missing values in `zulup_backup.json` are filled from defaults, and local values override defaults.
* `zulup_scan.json`: Controls how scanning continues below a directory.

If both files exist in the same directory, `zulup` raises an error.

Rationale: A directory is either a backup root (`zulup_backup.json`) or a scan router (`zulup_scan.json`). Mixing both roles in one directory is ambiguous and therefore forbidden.

## zulup_scan.json

Purpose: speed up discovery in large trees.

`zulup_scan.json` contains a JSON list of patterns.

```json
[
  "project_*",
  "dir_A",
  "dir_B",
  "/mnt/external/project_xy"
]
```

Behavior:

* When `zulup_scan.json` is encountered, normal recursive descent below that directory stops.
* Scanning continues only for directories matched by entries in the list.
* Entries are matched with Python's `fnmatch` module.

Rationale: If a directory is known to contain many subdirectories but only a few relevant backup roots, `zulup_scan.json` prevents a full tree walk.

Examples:

* `["project_*"]`: Will search for `zulup_backup.json` in `project_xy` and `project_rs`.

* `"dir_A"`, `"dir_B"`: search these named directories.

* `"/mnt/external/project_xy"`: search this absolute directory explicitly.



## zulup_backup.json

This file contains instructions.


```json
{
  "backup_name": "project_xy",
  "directory_target": "/mnt/backup",
  "directory_src": ".",
  "directory_name_include": true,
  "ignore": "see below"
}
```

`directory_src` may be a relative or absolute path.

Example: `/home/maerki/project_xy/zulup_backup.json`

`zulup_backup.json` has set `"directory_src": "."`.

If `"directory_name_include": true` the added files are `project_xy/README.md`, `project_xy/image.jpg` ...

If `"directory_name_include": false` the added files are `README.md`, `image.jpg` ...

* Include/Exclude options

  ```json
  "ignore": [
    ".git/",
    "*.pyc",
    "__pycache__/",
    "!important.pyc"
  ]
  ```

  Patterns use `.gitignore`-style syntax based on Python's `fnmatch` module.

  Pattern syntax:
  * `*` matches everything except `/`
  * `?` matches any single character except `/`
  * `[seq]` matches any character in *seq*
  * `[!seq]` matches any character not in *seq*

  Rules:
  * A pattern ending with `/` matches only directories. Otherwise it matches only files.
  * A pattern starting with `!` is an include (overrides a previous exclude).
  * A pattern containing `/` (other than a trailing `/`) is matched against the relative path. Otherwise it is matched against the file/directory name only.
  * By default, all files and directories are included.
  * The first matching pattern wins (determines include/exclude).
  * Patterns without `!` prefix are excludes.

  Examples:
  * `"*.log"` — exclude all `.log` files
  * `".git/"` — exclude every directory named `.git` (top folder and all subfolders)
  * `"build/output/"` — exclude the `output` directory under `build` (path match)
  * `"!README.md"` — include `README.md` even if a previous pattern would exclude it

* `"backup_name": "<DIRECTORY_NAME>"`
  `<DIRECTORY_NAME>` indicates to use the directory name of `zulup_backup.json`.

## `metafile`

Metafile contains all files which were found at the time of the snapshot.

Only files whose `verb` is `added` or `modified` are added to the `tarfile` (incremental backup).

In the `files` array, `snapshot_datetime` records the snapshot in which the current `verb` was assigned.

```json
{
    "backup" : {
        "backup_name": "project_xy",
        "parent": "/home/maerki/Downloads",
        "hostname": "maerki-ideapad-320"
    },
    "current": {
        "snapshot_datetime": "2026-04-03_14-22-22",
        "snapshot_type": "incr",
        "snapshot_stem": "project_xy_2026-04-03_14-22-22_incr",
        "tarfile_size": 1234
    },
    "history": [
        {
            "snapshot_datetime": "2026-04-03_12-22-22",
            "snapshot_type": "full",
            "snapshot_stem": "project_xy_2026-04-03_12-22-22_full",
            "tarfile_size": 1234
        },
        {
            "snapshot_datetime": "2026-04-03_13-22-22",
            "snapshot_type": "incr",
            "snapshot_stem": "project_xy_2026-04-03_13-22-22_incr",
            "tarfile_size": 1234
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

* Loop over the directory structure and discover backup roots based on `zulup_backup.json` and `zulup_scan.json`.
* For each backup:
  * Do minimal checks
    * Traverse `directory_src` and collect files according to `ignore`: We call it `current_filelist`.
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
  * Read the file size of `<directory_target>/<snapshot_stem>.tgz_tmp` and store it as `tarfile_size` in `current` of `new_metafile`.
  * Store `new_metafile` in `<directory_target>/<snapshot_stem>.json`.
  * Rename `<snapshot_stem>.tgz_tmp` to `<snapshot_stem>.tgz`

## Tar

* Tar files always have the suffix .tgz
* On windows: Use compression `-zcf` (gzip, as zstd is not available)
* Else: Use compression `--zstd -cf`

## systemd-inhibit - linux only

While the backup is running linux should not go sleep or shutdown.

**Implementation**

This is achieved with

```bash
systemd-inhibit --who=zulup --what=shutdown:sleep sleep infinity
```

This command will be called by `zulup` just after program start.

The termination of `zulup` must also terminate `systemd-inhibit`.

This is achieved with the kernel *Process Control* `prctl`:

```python
import subprocess
import ctypes

# Load the standard C library to access prctl
libc = ctypes.CDLL("libc.so.6")
PR_SET_PDEATHSIG = 1
SIGTERM = 15

def set_death_signal():
    # This function runs in the CHILD process just before systemd-inhibit starts
    libc.prctl(PR_SET_PDEATHSIG, SIGTERM)

cmd = [
    "systemd-inhibit",
    "--who=zulup",
    "--why=Backup in progress",
    "sleep", "infinity"
]

# preexec_fn ensures child gets SIGTERM when parent dies
process = subprocess.Popen(cmd, preexec_fn=set_death_signal)
```

On normal exit, `zulup` must explicitly call `process.terminate()` and `process.wait()` to clean up the `sleep infinity` process.

## zulup command line syntax

```bash
zulup backup <directories>
```

Searches <directories> for `zulup_backup.json` / `zulup_scan.json` files.
For every `zulup_backup.json` found, a backup is done.

```bash
zulup backup --full <directories>
```

As above, but does a full backup.

```bash
zulup snapshots <directory>
```

Reads `<directory>/zulup_backup.json` and lists all paths to metafiles for all snapshots.

```bash
zulup list <absolute-path-to-metafile.json>
```

Lists all files in this snapshot.

```bash
zulup restore <absolute-path-to-metafile.json> file-a file-b
```

Restores file-a and file-b into the current directory. All files are restored if no files are given.

## Implementation

* Naming of variables/properties of filenames
  * good: filename_xy
  * bad: path_xy

* Naming of variables/properties of directories
  * good: directory_xy
  * bad: path_xy

* Always use ISO units in the variable/property name. Always singular.
  * good: duration_s
  * bad: started_at