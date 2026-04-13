from __future__ import annotations

import dataclasses
import json
import pathlib
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

    @property
    def calculated_total(self) -> Decimal:
        return int(self.anzahl) * Decimal(self.preis)


@dataclasses.dataclass(slots=True, frozen=True)
class RechnungData:
    address1: str
    address2: str
    city: str
    comments: str
    company1: str
    company2: str
    datum: str
    einschreiben: str
    email: str
    firstname: str
    ftotal: str
    ftotalmwst: str
    g: str
    gewichttotal: str
    invoice_address1: str
    invoice_address2: str
    invoice_city: str
    invoice_company1: str
    invoice_company2: str
    invoice_firstname: str
    invoice_lastname: str
    invoice_zipcode: str
    land: str
    lastname: str
    lieferadresse: str
    lieferadresseinfo: str
    phone: str
    priority: str
    rechnungsadresse: str
    versandkosten: str
    za: str
    zeit: str
    zipcode: str
    positionen: list[Position] = dataclasses.field(default_factory=list)

    @property
    def calculated_fTotalCHF(self) -> Decimal:
        def _decimal_or_zero(value: str) -> Decimal:
            normalized = value.strip().replace(",", ".")
            if normalized == "":
                return Decimal("0")
            return Decimal(normalized)

        total = Decimal("0")
        for position in self.positionen:
            total += position.calculated_total

        total += _decimal_or_zero(self.versandkosten)
        return total

    @property
    def fTotalCHF(self) -> Decimal:
        return Decimal(self.ftotal)

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

        positionen = [Position(**p) for p in data_raw.pop("positionen")]
        return RechnungData(positionen=positionen, **data_raw)

    def write_datamatrix_png(self, filename_png: pathlib.Path) -> None:
        """
        Generate a Data Matrix barcode with content YYMMDDHHmmSS<email> and save as PNG.
        out_path: output PNG file
        """
        datetime = f"{self.datum[2:]}{self.zeit}".replace("-", "")
        code = f'"{datetime}{self.email}"'

        barcode = treepoem.generate_barcode(
            barcode_type="datamatrix",
            data=code,
            options={"borderwidth": "10"},
        )
        barcode.convert("1").save(filename_png)
