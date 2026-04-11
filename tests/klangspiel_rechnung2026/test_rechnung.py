from __future__ import annotations

import pathlib

from klangspiel_rechnung2026 import util_typst
from klangspiel_rechnung2026.util_jinja import render
from klangspiel_rechnung2026.util_xml import XmlParser

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTDATA_XML = DIRECTORY_OF_THIS_FILE / "testdata_xml"
DIRECTORY_TESTDATA_RESULT = DIRECTORY_OF_THIS_FILE / "testdata_xml_result"
DIRECTORY_TESTDATA_RESULT.mkdir(parents=True, exist_ok=True)


def test_rechnung() -> None:
    filename_xml = (
        DIRECTORY_TESTDATA_XML
        / "z_rechnung_vorlage_webshop_excel.beispielbestellung.txt"
    )
    data = XmlParser.parse_file(filename_xml=filename_xml)
    text_typ = render(data)

    filename_typst = (
        DIRECTORY_TESTDATA_RESULT
        / "z_rechnung_vorlage_webshop_excel.beispielbestellung.typ"
    )
    filename_typst.write_text(text_typ, encoding="utf-8")

    util_typst.render_pdf(
        text_typ=text_typ, filename_pdf=filename_typst.with_suffix(".pdf")
    )

    assert data.adresse.startswith("Fornerod Jean-Claude")
    assert len(data.positionen) == 1
    assert data.positionen[0].preis == "98.00"
    assert "RECHNUNG" in text_typ
    assert "#table(" in text_typ
    assert "[Anzahl]" in text_typ
    assert "[Einheit]" in text_typ
    assert "[1]," in text_typ
    assert "[Stück]," in text_typ
    assert "*Total CHF:* 104.30" in text_typ
    assert filename_typst.read_text(encoding="utf-8") == text_typ
