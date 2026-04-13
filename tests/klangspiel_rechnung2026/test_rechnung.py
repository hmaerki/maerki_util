from __future__ import annotations

import pathlib

import pytest

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


@pytest.fixture(
    params=sorted(
        path for path in DIRECTORY_TESTDATA_XML.iterdir() if path.suffix == ".xml"
    ),
    ids=lambda path: path.name,
)
def filename_xml(request: pytest.FixtureRequest) -> pathlib.Path:
    return request.param


def test_rechnung(filename_xml: pathlib.Path) -> None:
    filename_json = DIRECTORY_TESTDATA_RESULT / f"{filename_xml.stem}.json"

    data1 = util_xml.XmlParser.parse_file(filename_xml=filename_xml)

    filename_datamatrix_png = filename_json.with_suffix(".png")
    data1.write_datamatrix_png(filename_datamatrix_png)
    data1.write_json(filename_json)

    diffCHF = data1.fTotalCHF - data1.calculated_fTotalCHF
    assert abs(diffCHF) < 0.10, (data1.fTotalCHF, data1.calculated_fTotalCHF)

    data2 = util_dataclasses.RechnungData.read_json(filename_json)
    text_typ = util_jinja2.render(
        data2, filename_datamatrix_png=filename_datamatrix_png
    )

    filename_typst = DIRECTORY_TESTDATA_RESULT / f"{filename_xml.stem}.typ"
    filename_typst.write_text(text_typ, encoding="utf-8")

    util_typst.render_pdf(
        text_typ=text_typ, filename_pdf=filename_typst.with_suffix(".pdf")
    )
