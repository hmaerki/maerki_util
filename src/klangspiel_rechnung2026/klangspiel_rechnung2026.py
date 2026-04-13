from __future__ import annotations

import logging
import pathlib
import subprocess
import typing

import typer

from . import util_dataclasses, util_jinja2, util_logging, util_typst, util_xml

logger = logging.getLogger(__file__)


app = typer.Typer()


@app.command()
def clipboard(
    debug: typing.Annotated[
        bool,
        typer.Option("--debug", help="Set log level to DEBUG (default: INFO)"),
    ] = False,
) -> None:
    util_logging.init_logging(debug)

    result = subprocess.run(
        ["xsel", "--clipboard", "--output"],
        capture_output=True,
        text=True,
        check=True,
    )
    clipboard_text = result.stdout

    data = util_xml.XmlParser.parse_text(clipboard_text)
    print(f"{data.firstname} {data.lastname}: {len(data.positionen)} positionen")
    rechnung_nr = input("Rechnung (Beispiel: 20260303_01): ")

    def input_erhalten() -> bool:
        while True:
            erhalten_text = input("Zahlung erhalten [y/n]: ").strip()
            if erhalten_text == "y":
                return True
            if erhalten_text == "n":
                return False

    erhalten = input_erhalten()
    data2 = data.replace(
        erhalten=erhalten,
        rechnung_nr=rechnung_nr,
    )

    directory_top = pathlib.Path.cwd()

    if debug:
        (directory_top / "clipboard.xml").write_text(clipboard_text)

    data2.xml_json_pdf(debug=debug, directory_top=directory_top)


@app.command()
def json_update(
    debug: typing.Annotated[
        bool,
        typer.Option("--debug", help="Set log level to DEBUG (default: INFO)"),
    ] = False,
) -> None:
    """Update all .typ and .pdf files from JSONs in the directory."""

    util_logging.init_logging(debug)

    result_dir = pathlib.Path("tests/klangspiel_rechnung2026/testdata_xml_result")
    for json_file in sorted(result_dir.glob("*.json")):
        typ_file = json_file.with_suffix(".typ")
        pdf_file = json_file.with_suffix(".pdf")
        datamatrix_file = json_file.with_suffix(".datamatrix.png")
        logging.info(
            f"Updating {typ_file}, {pdf_file}, {datamatrix_file} from {json_file}"
        )
        data = util_dataclasses.RechnungData.read_json(json_file)
        text_typ = util_jinja2.render(
            data,
            filename_datamatrix_png=json_file.with_suffix(".png"),
        )
        typ_file.write_text(text_typ, encoding="utf-8")
        util_typst.render_pdf(text_typ=text_typ, filename_pdf=pdf_file)
        data.write_datamatrix_png(filename_png=json_file.with_suffix(".png"))


if __name__ == "__main__":
    app()
