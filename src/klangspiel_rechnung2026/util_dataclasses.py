from __future__ import annotations

import dataclasses
import json
import pathlib
import re
import typing
from decimal import Decimal

import treepoem


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
    fTotal: str
    g: str

    @property
    def calculated_fTotalCHF(self) -> Decimal:
        def _decimal_or_zero(value: str) -> Decimal:
            normalized = value.strip().replace(",", ".")
            if normalized == "":
                return Decimal("0")
            return Decimal(normalized)

        total = Decimal("0")
        for position in self.positionen:
            anzahl = _decimal_or_zero(position.anzahl)
            preis = _decimal_or_zero(position.preis)
            total += anzahl * preis

        total += _decimal_or_zero(self.versandkosten)
        return total

    @property
    def fTotalCHF(self) -> Decimal:
        return Decimal(self.fTotal)

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
            fTotal=RechnungData._value_as_str(data_dict, "fTotal"),
            g=RechnungData._value_as_str(data_dict, "g"),
        )

    def write_datamatrix_png(self, filename_png: pathlib.Path) -> None:
        """
        Generate a Data Matrix barcode with content YYMMDDHHmmSS<email> and save as PNG.
        out_path: output PNG file
        """
        # try:
        #     y, m, d = self.datum.split("-")
        #     h, mi, s = self.zeit.split("-")
        #     code = f"{y[2:]}{m}{d}{h}{mi}{s}{self.email}"
        # except Exception as e:
        #     raise ValueError(
        #         f"Invalid datum/zeit format: {self.datum} {self.zeit}"
        #     ) from e
        datetime = f"{self.datum[2:]}{self.zeit}".replace("-", "")
        code = f"{datetime}{self.email}"

        barcode = treepoem.generate_barcode(
            barcode_type="datamatrix",
            data=code,
            options={"borderwidth": "10"},
        )
        barcode.convert("1").save(filename_png)


POSITION_TAG_RE = re.compile(r"^Pos(?P<idx>\d+)(?P<field>Anzahl|wo|Unit|Text|Preis)$")
