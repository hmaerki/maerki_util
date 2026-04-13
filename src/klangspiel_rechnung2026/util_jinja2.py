from __future__ import annotations

import decimal
import pathlib

import jinja2

from . import util_dataclasses

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


def render(
    data: util_dataclasses.RechnungData, filename_datamatrix_png: pathlib.Path
) -> str:
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
    template = env.from_string(template_text)
    rendered = template.render(
        data=data,
        filename_datamatrix_png=filename_datamatrix_png.name,
    )
    return rendered.rstrip() + "\n"
