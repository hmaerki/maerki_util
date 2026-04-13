from __future__ import annotations

import pathlib

import typst  # type: ignore[import-not-found]


def render_pdf(text_typ: str, filename_pdf: pathlib.Path) -> None:
    filename_pdf.parent.mkdir(parents=True, exist_ok=True)
    typst.compile(text_typ.encode(), root=filename_pdf.parent, output=str(filename_pdf))  # type: ignore[attr-defined]
