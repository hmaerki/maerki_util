from __future__ import annotations

import dataclasses
import re
import typing


@dataclasses.dataclass(slots=True, frozen=True)
class Position:
    anzahl: str
    wo: str
    unit: str
    text: str
    preis: str


@dataclasses.dataclass(slots=True, frozen=True)
class RechnungData:
    adresse: str
    telefon: str
    email: str
    bemerkungen: str
    za: str
    datum: str
    zeit: str
    positionen: list[Position]
    gewicht_total: str
    versandkosten: str
    versandkosten_eu: str
    total_chf: str
    g: str


_POSITION_TAG_RE = re.compile(r"^Pos(?P<idx>\d+)(?P<field>Anzahl|wo|Unit|Text|Preis)$")


def _clean_value(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _position_sort_key(item: tuple[int, dict[str, str]]) -> int:
    return item[0]


def parse_positions(xml_values: typing.Mapping[str, str]) -> list[Position]:
    positions_raw: dict[int, dict[str, str]] = {}
    for key, value in xml_values.items():
        match = _POSITION_TAG_RE.match(key)
        if match is None:
            continue
        idx = int(match.group("idx"))
        field = match.group("field")
        fields = positions_raw.setdefault(idx, {})
        fields[field] = _clean_value(value)

    positions: list[Position] = []
    for _idx, fields in sorted(positions_raw.items(), key=_position_sort_key):
        positions.append(
            Position(
                anzahl=fields.get("Anzahl", ""),
                wo=fields.get("wo", ""),
                unit=fields.get("Unit", ""),
                text=fields.get("Text", ""),
                preis=fields.get("Preis", ""),
            )
        )
    return positions


def from_xml_values(xml_values: typing.Mapping[str, str]) -> RechnungData:
    return RechnungData(
        adresse=_clean_value(xml_values.get("Adresse")),
        telefon=_clean_value(xml_values.get("Telefon")),
        email=_clean_value(xml_values.get("Email")),
        bemerkungen=_clean_value(xml_values.get("Bemerkungen")),
        za=_clean_value(xml_values.get("za")),
        datum=_clean_value(xml_values.get("Datum")),
        zeit=_clean_value(xml_values.get("Zeit")),
        positionen=parse_positions(xml_values),
        gewicht_total=_clean_value(xml_values.get("GewichtTotal")),
        versandkosten=_clean_value(xml_values.get("Versandkosten")),
        versandkosten_eu=_clean_value(xml_values.get("VersandkostenEU")),
        total_chf=_clean_value(xml_values.get("total_chf")),
        g=_clean_value(xml_values.get("g")),
    )
