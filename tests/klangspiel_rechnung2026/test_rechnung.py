from __future__ import annotations

import pathlib

import pytest
import shutil

from klangspiel_rechnung2026 import util_dataclasses, util_jinja2, util_typst, util_xml

# pylint: disable=redefined-outer-name
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA_XML = DIRECTORY_OF_THIS_FILE / "testdata_xml"
DIRECTORY_TESTDATA_RESULT = DIRECTORY_OF_THIS_FILE / "testdata_xml_result"
DIRECTORY_TESTDATA_RESULT.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def cleanup_result_directory() -> None:
    for path in DIRECTORY_TESTDATA_RESULT.iterdir():
        if path.is_file():
            path.unlink()
        if path.is_dir():
            shutil.rmtree(path)


@pytest.fixture(
    params=sorted(
        path for path in DIRECTORY_TESTDATA_XML.iterdir() if path.suffix == ".xml"
    ),
    ids=lambda path: path.name,
)
def filename_xml(request: pytest.FixtureRequest) -> pathlib.Path:
    return request.param


@pytest.mark.parametrize(
    "rechnung_nr,erhalten",
    (
        ("", False),
        ("123", True),
    ),
)
def test_rechnung(filename_xml: pathlib.Path, rechnung_nr: str, erhalten: bool) -> None:
    rechnung_nr2 = f"_{rechnung_nr}" if rechnung_nr else ""
    directory_top = DIRECTORY_TESTDATA_RESULT / f"{filename_xml.stem}{rechnung_nr2}"

    data0 = util_xml.XmlParser.parse_file(filename_xml=filename_xml)
    data1 = data0.replace(erhalten=erhalten, rechnung_nr=rechnung_nr)

    data1.xml_json_pdf(debug=True, directory_top=directory_top)

    # diffCHF = data1.fTotalCHF - data1.calculated_fTotalCHF
    # assert abs(diffCHF) < 0.10, (data1.fTotalCHF, data1.calculated_fTotalCHF)
