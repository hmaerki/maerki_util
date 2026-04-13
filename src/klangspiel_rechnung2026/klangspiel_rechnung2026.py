from __future__ import annotations

import logging
import pathlib
import typing

import typer

from klangspiel_rechnung2026 import util_typst
from klangspiel_rechnung2026.util_dataclasses import RechnungData
from klangspiel_rechnung2026.util_jinja import render
from klangspiel_rechnung2026.util_logging import init_logging

logger = logging.getLogger(__file__)


app = typer.Typer()


@app.command()
def update(
    debug: typing.Annotated[
        bool,
        typer.Option("--debug", help="Set log level to DEBUG (default: INFO)"),
    ] = False,
) -> None:
    """Update all .typ and .pdf files from JSONs in the directory."""

    init_logging(debug)

    result_dir = pathlib.Path("tests/klangspiel_rechnung2026/testdata_xml_result")
    for json_file in sorted(result_dir.glob("*.json")):
        typ_file = json_file.with_suffix(".typ")
        pdf_file = json_file.with_suffix(".pdf")
        datamatrix_file = json_file.with_suffix(".datamatrix.png")
        logging.info(
            f"Updating {typ_file}, {pdf_file}, {datamatrix_file} from {json_file}"
        )
        data = RechnungData.read_json(json_file)
        text_typ = render(data)
        typ_file.write_text(text_typ, encoding="utf-8")
        util_typst.render_pdf(text_typ=text_typ, filename_pdf=pdf_file)
        data.write_datamatrix_png(filename_png=json_file.with_suffix(".png"))


@app.command()
def create(
    debug: typing.Annotated[
        bool,
        typer.Option("--debug", help="Set log level to DEBUG (default: INFO)"),
    ] = False,
) -> None:
    init_logging(debug)

    # Example: read XML, parse to RechnungData, then write datamatrix.png
    # (Assume filename_xml is a required argument for create)
    import typer
    from klangspiel_rechnung2026.util_xml import XmlParser

    filename_xml = typer.prompt("XML file path")
    data = XmlParser.parse_file(pathlib.Path(filename_xml))
    data.write_datamatrix_png(filename_png=filename_xml.with_suffix(".png"))


if __name__ == "__main__":
    app()
