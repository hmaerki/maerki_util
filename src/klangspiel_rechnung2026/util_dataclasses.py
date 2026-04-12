from __future__ import annotations

import dataclasses
import json
import pathlib
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

    def write_json(self, filename_json: pathlib.Path) -> None:
        filename_json.write_text(
            json.dumps(dataclasses.asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _value_as_str(data_dict: dict[str, typing.Any], key: str) -> str:
        value = data_dict[key]
        if not isinstance(value, str):
            raise TypeError(f"Expected {key!r} to be str, got {type(value).__name__}")
        return value

    @staticmethod
    def read_json(filename_json: pathlib.Path) -> RechnungData:
        data_raw = json.loads(filename_json.read_text(encoding="utf-8"))
        if not isinstance(data_raw, dict):
            raise TypeError("Expected top-level JSON object")
        data_dict = typing.cast(dict[str, typing.Any], data_raw)

        positionen_raw = data_dict.get("positionen")
        if not isinstance(positionen_raw, list):
            raise TypeError("Expected 'positionen' to be a list")

        positionen: list[Position] = []
        for position_raw in positionen_raw:
            if not isinstance(position_raw, dict):
                raise TypeError("Expected each position to be an object")
            position_dict = typing.cast(dict[str, typing.Any], position_raw)
            positionen.append(
                Position(
                    anzahl=RechnungData._value_as_str(position_dict, "anzahl"),
                    wo=RechnungData._value_as_str(position_dict, "wo"),
                    unit=RechnungData._value_as_str(position_dict, "unit"),
                    text=RechnungData._value_as_str(position_dict, "text"),
                    preis=RechnungData._value_as_str(position_dict, "preis"),
                )
            )

        return RechnungData(
            adresse=RechnungData._value_as_str(data_dict, "adresse"),
            telefon=RechnungData._value_as_str(data_dict, "telefon"),
            email=RechnungData._value_as_str(data_dict, "email"),
            bemerkungen=RechnungData._value_as_str(data_dict, "bemerkungen"),
            za=RechnungData._value_as_str(data_dict, "za"),
            datum=RechnungData._value_as_str(data_dict, "datum"),
            zeit=RechnungData._value_as_str(data_dict, "zeit"),
            positionen=positionen,
            gewicht_total=RechnungData._value_as_str(data_dict, "gewicht_total"),
            versandkosten=RechnungData._value_as_str(data_dict, "versandkosten"),
            versandkosten_eu=RechnungData._value_as_str(data_dict, "versandkosten_eu"),
            total_chf=RechnungData._value_as_str(data_dict, "total_chf"),
            g=RechnungData._value_as_str(data_dict, "g"),
        )


POSITION_TAG_RE = re.compile(r"^Pos(?P<idx>\d+)(?P<field>Anzahl|wo|Unit|Text|Preis)$")
