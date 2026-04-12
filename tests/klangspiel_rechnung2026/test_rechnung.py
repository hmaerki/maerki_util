from __future__ import annotations

import pathlib

import pytest

from klangspiel_rechnung2026 import util_typst
from klangspiel_rechnung2026.util_dataclasses import RechnungData
from klangspiel_rechnung2026.util_jinja import render
from klangspiel_rechnung2026.util_xml import XmlParser

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
    params=sorted(path for path in DIRECTORY_TESTDATA_XML.iterdir() if path.is_file()),
    ids=lambda path: path.name,
)
def filename_xml(request: pytest.FixtureRequest) -> pathlib.Path:
    return request.param


def test_rechnung(filename_xml: pathlib.Path) -> None:
    data1 = XmlParser.parse_file(filename_xml=filename_xml)

    filename_json = DIRECTORY_TESTDATA_RESULT / f"{filename_xml.stem}.json"
    data1.write_json(filename_json)

    data2 = RechnungData.read_json(filename_json)
    text_typ = render(data2)

    filename_typst = DIRECTORY_TESTDATA_RESULT / f"{filename_xml.stem}.typ"
    filename_typst.write_text(text_typ, encoding="utf-8")

    util_typst.render_pdf(
        text_typ=text_typ, filename_pdf=filename_typst.with_suffix(".pdf")
    )

    # assert data.adresse.startswith("Fornerod Jean-Claude")
    # assert len(data.positionen) == 1
    # assert data.positionen[0].preis == "98.00"
    # assert "RECHNUNG" in text_typ
    # assert "#table(" in text_typ
    # assert "[Anzahl]" in text_typ
    # assert "[Einheit]" in text_typ
    # assert "[1]," in text_typ
    # assert "[Stück]," in text_typ
    # assert "*Total CHF:* 104.30" in text_typ
    # assert filename_typst.read_text(encoding="utf-8") == text_typ
