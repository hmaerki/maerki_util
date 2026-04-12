from __future__ import annotations

import pathlib
from decimal import Decimal

from klangspiel_rechnung2026.util_dataclasses import RechnungData


def _typst_escape(value: str) -> str:
    # Keep plain text semantics for user content inside Typst markup/content mode.
    return (
        value.replace("\\", "\\\\")
        .replace("@", "\\@")
        .replace("#", "\\#")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("*", "\\*")
    )


def _typst_cell(value: str) -> str:
    return _typst_escape(value.replace("\n", " ").strip())


def _format_position_rows(data: RechnungData) -> str:
    lines: list[str] = []
    for pos in data.positionen:
        lines.extend(
            [
                f"  [{_typst_cell(pos.anzahl)}],",
                f"  [{_typst_cell(pos.unit)}],",
                f"  [{_typst_cell(pos.wo)}],",
                f"  [{_typst_cell(pos.text)}],",
                f"  [CHF {_typst_cell(pos.preis)}],",
            ]
        )
    return "\n".join(lines)


def render(data: RechnungData, filename_template: pathlib.Path | None = None) -> str:
    if filename_template is None:
        filename_template = pathlib.Path(__file__).with_name("template.jinja")
    template = filename_template.read_text(encoding="utf-8")

    rendered = template.format(
        adresse=_typst_escape(data.adresse),
        telefon=_typst_escape(data.telefon),
        email=_typst_escape(data.email),
        bemerkungen=_typst_escape(data.bemerkungen),
        za=_typst_escape(data.za),
        datum=_typst_escape(data.datum),
        zeit=_typst_escape(data.zeit),
        position_rows=_format_position_rows(data),
        gewicht_total=_typst_escape(data.gewicht_total),
        versandkosten=_typst_escape(data.versandkosten),
        versandkosten_eu=_typst_escape(data.versandkosten_eu),
        calculated_fTotalCHF=_typst_escape(
            f"{data.calculated_fTotalCHF.quantize(Decimal('0.01'))}"
        ),
        g=_typst_escape(data.g),
    )
    return rendered.rstrip() + "\n"
