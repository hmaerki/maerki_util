from __future__ import annotations

from zulup.util_json_metafile import EnumVerb
from zulup.util_pytest import TestProjectDirectory


def test_backup_incr(project: TestProjectDirectory) -> None:
    project.create_file("a.txt", "a-v1\n")
    project.create_file("b.txt", "b-v1\n")
    project.create_file("c.txt", "c-v1\n")

    project.create_zulup_json(directory_name_include=False, ignore=[".git/"])

    # create first full backup
    project.do_backup(snapshot_datetime="2026-04-07_10-00-00")

    # Modify files and create second incremental backup
    project.create_file("d.txt", "d-v1\n")
    project.create_file("b.txt", "b-v2-modified\n")
    (project.src / "c.txt").unlink()

    project.do_backup(snapshot_datetime="2026-04-07_10-00-01")

    backup_directory = project.get_backup_directory()
    assert len(backup_directory.snapshots) == 2

    full_metafile = backup_directory.snapshots[0].metafile
    incr_metafile = backup_directory.snapshots[1].metafile
    assert (project.target / full_metafile.current.tarfile_name).is_file()
    assert (project.target / incr_metafile.current.tarfile_name).is_file()
    assert full_metafile.current.tarfile_size is not None
    assert full_metafile.current.tarfile_size > 0
    assert incr_metafile.current.tarfile_size is not None
    assert incr_metafile.current.tarfile_size > 0

    assert full_metafile.current.snapshot_type == "full"
    assert incr_metafile.current.snapshot_type == "incr"
    assert len(incr_metafile.history) == 1
    assert incr_metafile.history[0].snapshot_type == "full"

    files_by_path = {entry.path: entry for entry in incr_metafile.files}
    assert files_by_path["a.txt"].verb == EnumVerb.UNTOUCHED
    assert files_by_path["b.txt"].verb == EnumVerb.MODIFIED
    assert files_by_path["c.txt"].verb == EnumVerb.REMOVED
    assert files_by_path["d.txt"].verb == EnumVerb.ADDED
