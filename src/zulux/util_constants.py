import datetime

ZULUX_CHMOD_JSON_SUFFIX = "zulux_chmod.json"
README_URL = "https://github.com/hmaerki/maerki_util/blob/zulup/src/zulux/README.md"
SNAPSHOT_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def now_text() -> str:
    return datetime.datetime.now().strftime(SNAPSHOT_DATETIME_FORMAT)
