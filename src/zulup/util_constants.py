import datetime

TARFILE_SUFFIX = ".tgz"
METAFILE_SUFFIX = ".json"
ZULUP_BACKUP_JSON = "zulup_backup.json"
ZULUP_SCAN_JSON = "zulup_scan.json"
SNAPSHOT_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def now_text() -> str:
    return datetime.datetime.now().strftime(SNAPSHOT_DATETIME_FORMAT)
