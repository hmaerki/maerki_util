import base64
import dataclasses
import http
import http.client
import io
import json
import logging
import pathlib
import re
import socket
import ssl
from urllib import parse as urlparse

import typer

logger = logging.getLogger(__file__)

# The WebDAV-Protocol is specified here:
# http://www.webdav.org/specs/rfc2518.html

# HISTORY

# 1.1.7
# Upload will be done in four rounds
# 0: First all .html and .css
# 1: Then all files smaller than 100k
# 2: Then all files smaller than 5M
# 3: Rest

# ----------------------------------------------------------------------------

sCopyright = "Copyright Hans Maerki. LGPL."
sVersion = "v1.1.8"
sProduct = "HTTP Upload"

# ----------------------------------------------------------------------------

FILENAME_HTTP_UPLOAD_CREDENTIALS = (
    pathlib.Path("~/private/http_upload_credentials.json").expanduser().absolute()
)
FILENAME_HTTP_UPLOAD_CONFIG = pathlib.Path("http_upload_config.json").absolute()


@dataclasses.dataclass(frozen=True)
class HttpUploadCredential:
    name: str
    user: str
    password: str

    @property
    def user_password(self) -> str:
        v = ":".join([self.user, self.password])
        v = base64.encodebytes(bytes(v, "utf-8"))
        return v.decode("utf-8").replace("\n", "")


class HttpUploadCredentials(list[HttpUploadCredential]):
    @classmethod
    def load(cls, credentials_file: pathlib.Path) -> "HttpUploadCredentials":
        data = json.loads(credentials_file.read_text(encoding="utf-8"))
        return cls(HttpUploadCredential(**entry) for entry in data)

    def get_credential(self, name: str) -> HttpUploadCredential:
        for credential in self:
            if credential.name == name:
                return credential
        raise KeyError()


@dataclasses.dataclass(frozen=True)
class HttpUploadConfig:
    config_version: str
    name: str
    local: str
    remote: str
    exclude: list[str]

    @classmethod
    def load(cls, config_file: pathlib.Path) -> "HttpUploadConfig":
        data = json.loads(config_file.read_text(encoding="utf-8"))
        return cls(**data)


# ----------------------------------------------------------------------------

#
# The command-line-interface and the user-interface each use
# a Mediator-Class as an interface to HttpUpload.
#


# ----------------------------------------------------------------------------


# ----------------------------------------------------------------------------

UPLOAD_ROUNDS = 4


class HttpUpload:
    def __init__(self, config_file: pathlib.Path, credentials_file: pathlib.Path):
        assert isinstance(config_file, pathlib.Path)
        assert isinstance(credentials_file, pathlib.Path)

        logger.info(f"Credentials: {credentials_file}")
        logger.info(f"Working directory: {config_file.parent}")
        logger.info(f"Read config: {config_file.name}")

        self.config_file = config_file
        self.config = HttpUploadConfig.load(config_file=config_file)
        credentials = HttpUploadCredentials.load(credentials_file=credentials_file)
        try:
            self.credential = credentials.get_credential(self.config.name)
        except KeyError:
            logger.error(
                f"File '{config_file}' refers to '{self.config.name}' which is not found in: {credentials_file}"
            )
            typer.Abort()

        self.dict_file_size_cache: dict[str, int] = {}
        self.dict_file_time_cache: dict[str, int] = {}
        self.objConnection = None
        (
            self.remote_protocol,
            self.remote_host,
            self.remote_path,
            dummy,
            dummy,
            dummy,
        ) = urlparse.urlparse(self.config.remote)
        self.directory_local_top = config_file.parent / self.config.local

        self.strAuthorization = f"Basic {self.credential.user_password}"

        self.filename_timestamps = (
            self.directory_local_top / "tmp_httpupload_timestamps_cache.txt"
        )

        self.iFilesUploaded = 0

        # Compile the regular expressions
        self.listRegexpExclude = [
            re.compile(e, re.IGNORECASE) for e in self.config.exclude
        ]

        self.listRegexpExclude.append(re.compile("\\.pyc$", re.IGNORECASE))
        self.listRegexpExclude.append(re.compile("/__pycache__/", re.IGNORECASE))
        self.listRegexpExclude.append(re.compile("\\.git$", re.IGNORECASE))

    def http_verb(
        self,
        verb: str,
        relative_path: str,
        f_page: io.BufferedReader | str = "",
    ) -> http.client.HTTPResponse:
        if self.objConnection is None:
            if self.remote_protocol == "https":
                sslContext = ssl.create_default_context()
                sslContext.check_hostname = False
                sslContext.verify_mode = ssl.CERT_NONE
                self.objConnection = http.client.HTTPSConnection(
                    self.remote_host,
                    context=sslContext,
                    timeout=30,
                )
            else:
                self.objConnection = http.client.HTTPConnection(
                    self.remote_host,
                    timeout=30,
                )

        headers = {
            "Accept": "text/html",
            "User-Agent": "httpupload",
            "Host": self.remote_host,
            # 'Content-Length': str(len(strPage)),
            "Authorization": self.strAuthorization,
        }

        try:
            full_relative_path = f"{self.remote_path}/{relative_path}"
            full_relative_path = full_relative_path.replace(" ", "%20")
            self.objConnection.request(verb, full_relative_path, f_page, headers)
            response = self.objConnection.getresponse()
            _data = response.read()
        except Exception as e:
            self.objConnection.close()
            self.objConnection = None
            logger.exception(e)
            raise Exception(f'"{verb}", "{relative_path}": "{e}"') from e
        return response

    def http_create_folder(self, relative_path: str) -> http.client.HTTPResponse:
        return self.http_verb("MKCOL", relative_path)

    def http_create_folder_recursive(self, relative_path: str) -> None:
        assert isinstance(relative_path, str)

        pos = relative_path.rfind("/")
        if pos <= 1:
            # There will never be more than 10 nested directories
            return
        sub_path = relative_path[:pos]
        response = self.http_create_folder(sub_path)
        if response.status != 201:
            self.http_create_folder_recursive(sub_path)
            self.http_create_folder(sub_path)

    def http_upload_file_put(
        self, filename: pathlib.Path, relative_path: str
    ) -> http.client.HTTPResponse:
        """return 0 if 0 error. return 1 if 1 error."""
        assert isinstance(filename, pathlib.Path)
        assert isinstance(relative_path, str)

        with filename.open("rb") as f:
            return self.http_verb("PUT", relative_path, f)

    def http_upload_file(self, filename: pathlib.Path) -> int:
        assert isinstance(filename, pathlib.Path)

        relative_path = str(filename.relative_to(self.directory_local_top))
        response = self.http_upload_file_put(filename, relative_path)
        if 200 <= response.status < 300:
            # SUCCESS
            # 201 Created.
            # 204 No Content (File ueberschrieben ...)
            return 0
        if response.status in (
            403,  # Forbidden
            409,  # Conflict. Missing one or more intermediate collections.
            # --> Folder missing
        ):
            self.http_create_folder_recursive(relative_path)
            response = self.http_upload_file_put(filename, relative_path)
            if response.status in (201, 204):
                return 0
        msg = f"{response.status} {response.reason}:   {self.remote_protocol}  ://  {self.remote_host}  {relative_path}"
        logger.warning(msg)
        raise UserWarning(msg)

        # self.objLogger.error(strMessage)
        return 1

    def skip_file(self, current_path: pathlib.Path) -> bool:
        """Returns if the filename ends with '.httpupload.skip'
        or there is a file ending with '.httpupload.skip'."""
        if current_path.name.endswith(".httpupload.skip"):
            return True
        if current_path.with_name(current_path.name + ".httpupload.skip").exists():
            # Path.exists() works for folders and for files
            return True
        if self.filename_timestamps == current_path:
            # This is the cache-file. Skip it.
            return True

        for reExp in self.listRegexpExclude:
            if reExp.search(str(current_path)):
                return True

        return False

    def upload_file(self, current_path: pathlib.Path) -> int:
        """return 0 if 0 error. return 1 if 1 error."""

        if self.skip_file(current_path):
            return 0
        relative_path = current_path.relative_to(self.directory_local_top)
        # url = f"{self.remote_protocol}://{self.remote_host}{self.remote_path}/{relative_path}"
        # url = f"{self.remote_protocol}://{self.remote_host}{self.remote_path}/{relative_path}"
        time_cached_ms = self.get_cache(str(relative_path))

        time_file_ms = self.dict_file_time_cache.setdefault(
            str(relative_path), int(1000*current_path.stat().st_mtime)
        )

        # If daylight savings (Sommerzeit), has an influence
        # on the POSIX time. I couldn't figure out, which
        # mechanism is used.
        # We used some fuzzy logic now.
        # if time_cached_ms >= 1000*attr.st_mtime:
        # if time_cached_ms >= time_file_ms:
        assert isinstance(time_cached_ms, int), time_cached_ms
        assert isinstance(time_file_ms, int), time_file_ms
        if time_file_ms in (time_cached_ms - 3600_000, time_cached_ms, time_cached_ms + 3600_000):
            # File hasn't changed
            return 0

        logger.debug(f"{self.iFilesUploaded + 1}: File '{relative_path}'")

        error_count = self.http_upload_file(current_path)
        if error_count == 0:
            # self.dict_last_modification_times[strPath] = attr.st_mtime
            self.add_cache(str(relative_path), time_file_ms)

        return error_count

    def select_file(self, current_path: pathlib.Path, round: int) -> bool:
        assert isinstance(current_path, pathlib.Path)
        assert isinstance(round, int)
        if round == 0:
            if current_path.suffix in (".html", ".css", ".htaccess"):
                return True
            return False

        # Cache the filesize
        filename_relative = str(current_path.relative_to(self.directory_local_top))
        size = self.dict_file_size_cache.setdefault(
            filename_relative, current_path.stat().st_size
        )

        if round == 1:
            return size < 100 * 1000
        if round == 2:
            return size < 5 * 1000 * 1000
        assert round < UPLOAD_ROUNDS
        return True

    def recurse_folder(self, current_path: pathlib.Path, round: int) -> int:
        """returns the error count"""
        assert isinstance(current_path, pathlib.Path)
        assert isinstance(round, int)

        error_count = 0
        for sub_path in current_path.iterdir():
            if not self.skip_file(sub_path):
                if sub_path.is_dir():
                    error_count += self.recurse_folder(sub_path, round)
                else:
                    if self.select_file(sub_path, round):
                        error_count += self.upload_file(sub_path)
        return error_count

    def upload_2(self, round: int) -> int:
        assert isinstance(round, int)

        error_count = self.recurse_folder(self.directory_local_top, round)
        for i in range(2):
            if error_count == 0:
                return 0
            logger.error(
                f"{error_count} errors occurred during this loop! Trying a {i + 2}'d time."
            )
            error_count = self.recurse_folder(self.directory_local_top, round)
        return error_count

    def upload_1(self, force_upload: bool) -> int:
        self.dict_last_modification_times: dict[str, int] = {}
        if force_upload:
            self.file_timestamps = self.filename_timestamps.open("w")
        else:
            if self.filename_timestamps.exists():
                self.file_timestamps = self.filename_timestamps.open("r")
                for strLine in self.file_timestamps:
                    strLine = strLine.strip()
                    if len(strLine) == 0:
                        # Skip empty lines
                        continue
                    part = strLine.partition("\t")
                    strTime = part[0]
                    strPath = part[2]
                    # self.objLogger.info("-%d-%s-%s-" % (int(strTime), strPath, strLine))
                    self.dict_last_modification_times[strPath] = int(strTime)
            self.file_timestamps = self.filename_timestamps.open("a+")

        # for strPath, iTime in self.dict_last_modification_times.items():
        #  self.objLogger.warning("'%s':%i" % (strPath, iTime))

        error_count = 0
        for round in range(UPLOAD_ROUNDS):
            error_count += self.upload_2(round)
            if self.objConnection is not None:
                # After a run, we might run into a timeout.
                # Closing the connection could be a bit more stable
                self.file_timestamps.flush()
                self.objConnection.close()
                self.objConnection = None
            if error_count > 0:
                break

        self.file_timestamps.close()
        if self.iFilesUploaded > 0:
            # Purge duplicated entries
            self.file_timestamps = open(self.filename_timestamps, "w")
            for strPath in sorted(self.dict_last_modification_times.keys()):
                iTime = self.dict_last_modification_times[strPath]
                self.file_timestamps.write(f"{iTime}\t{strPath}\n")

        logger.info(f"{self.iFilesUploaded} Files uploaded.")

        if error_count == 0:
            logger.info("---- SUCCESS")
        else:
            logger.error("---- FAILED")

        return error_count

    def get_cache(self, relative_path: str) -> int:
        return self.dict_last_modification_times.get(relative_path, 0)

    def add_cache(self, relative_path: str, time_file_ms: int) -> None:
        assert isinstance(relative_path, str)
        assert isinstance(time_file_ms, int)
        self.iFilesUploaded = self.iFilesUploaded + 1
        self.file_timestamps.write(f"{time_file_ms}\t{relative_path}\n")
        self.dict_last_modification_times[relative_path] = time_file_ms

    def upload(self, force_upload: bool) -> int:
        try:
            return self.upload_1(force_upload=force_upload)
        except UserWarning as e:
            logger.error(f"{UserWarning}: {e}")
            return 1
        except socket.gaierror as e:
            logger.error(f'    Error: Host "{self.remote_host}" not found! {e}')
            return 1
        except Exception as e:
            logger.exception(e)
            return 1


# ----------------------------------------------------------------------------


def main(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force upload of all files",
    ),
) -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    assert FILENAME_HTTP_UPLOAD_CREDENTIALS.is_file(), FILENAME_HTTP_UPLOAD_CREDENTIALS
    assert FILENAME_HTTP_UPLOAD_CONFIG.is_file(), FILENAME_HTTP_UPLOAD_CONFIG

    http_upload = HttpUpload(
        config_file=FILENAME_HTTP_UPLOAD_CONFIG,
        credentials_file=FILENAME_HTTP_UPLOAD_CREDENTIALS,
    )
    http_upload.upload(force_upload=force)


if __name__ == "__main__":
    typer.run(main)
