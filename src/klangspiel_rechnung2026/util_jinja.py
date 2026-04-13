from __future__ import annotations

import decimal
import pathlib

import jinja2

from klangspiel_rechnung2026.util_dataclasses import Position, RechnungData

FILENAME_TEMPLATE = pathlib.Path(__file__).with_name("template.jinja")
assert FILENAME_TEMPLATE.is_file()


def _typst_escape(value: str) -> str:
    # Keep plain text semantics for user content inside Typst markup/content mode.
    return (
        value.replace("\\", "\\\\")
        .replace("@", "\\@")
        .replace("#", "\\#")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("*", "\\*")
    ).strip()


def _typst_address_block(data: RechnungData, prefix: str = "") -> str:
    lines: list[str] = []
    for field in ("company1", "company2"):
        value: str = getattr(data, f"{prefix}{field}")
        if value.strip():
            lines.append(_typst_escape(value))
    firstname: str = getattr(data, f"{prefix}firstname")
    lastname: str = getattr(data, f"{prefix}lastname")
    name = f"{_typst_escape(firstname)} {_typst_escape(lastname)}".strip()
    if name:
        lines.append(name)
    for field in ("address1", "address2"):
        value = getattr(data, f"{prefix}{field}")
        if value.strip():
            lines.append(_typst_escape(value))
    zipcode: str = getattr(data, f"{prefix}zipcode")
    city: str = getattr(data, f"{prefix}city")
    zip_city = f"{_typst_escape(zipcode)} {_typst_escape(city)}".strip()
    if zip_city:
        lines.append(zip_city)
    return " \\\n".join(lines)


def _line_total_filter(position: Position) -> str:
    anzahl = int(position.anzahl.strip())
    preis_str = position.preis.strip().replace(",", ".")
    if not preis_str:
        return "0.00"
    total = anzahl * decimal.Decimal(preis_str)
    return f"{total:.2f}"


def render(data: RechnungData) -> str:
    template_text = FILENAME_TEMPLATE.read_text(encoding="utf-8")

    def typ_filter(value: str) -> str:
        if isinstance(value, decimal.Decimal):
            return value
        assert isinstance(value, str), repr(value)
        return _typst_escape(value)

    env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["typ"] = typ_filter
    env.filters["line_total"] = _line_total_filter
    env.filters["invoice_address"] = lambda d: _typst_address_block(d, "invoice_")
    env.filters["delivery_address"] = lambda d: _typst_address_block(d, "")
    template = env.from_string(template_text)
    rendered = template.render(data=data)
    return rendered.rstrip() + "\n"
