from __future__ import annotations

import dataclasses
import json
import pathlib
import shutil
import typing
from decimal import Decimal

import treepoem

from . import util_jinja2, util_typst

DIRECTORY_RUN_TEMPLATES = pathlib.Path(__file__).parent
assert DIRECTORY_RUN_TEMPLATES.is_dir()

ORIGINAL_JSON = "original.json"
FILENAME_RECHNUNG_PDF = "rechnung.pdf"
FILENAME_SONNE_PNG = pathlib.Path(__file__).with_name("template_sonne.png")
assert FILENAME_SONNE_PNG.is_file()


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
class Adresse:
    address1: str
    address2: str
    city: str
    company1: str
    company2: str
    firstname: str
    lastname: str
    zipcode: str

    @property
    def is_empty(self) -> bool:
        return (
            self.address1
            + self.address2
            + self.city
            + self.company1
            + self.company2
            + self.firstname
            + self.lastname
            + self.zipcode
        ).strip() == ""


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
    rechnung_nr: str = ""
    erhalten: bool = False
    positionen: list[Position] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        assert isinstance(self.rechnung_nr, str)
        assert isinstance(self.erhalten, bool)

    @property
    def get_address(self) -> Adresse:
        return Adresse(
            address1=self.address1,
            address2=self.address2,
            city=self.city,
            company1=self.company1,
            company2=self.company2,
            firstname=self.firstname,
            lastname=self.lastname,
            zipcode=self.zipcode,
        )

    @property
    def get_invoice(self) -> Adresse:
        return Adresse(
            address1=self.invoice_address1,
            address2=self.invoice_address2,
            city=self.invoice_city,
            company1=self.invoice_company1,
            company2=self.invoice_company2,
            firstname=self.invoice_firstname,
            lastname=self.invoice_lastname,
            zipcode=self.invoice_zipcode,
        )

    @property
    def get_rechnungsadresse(self) -> Adresse:
        invoice = self.get_invoice
        if invoice.is_empty:
            return self.get_address
        return invoice

    @property
    def rechnung_nr_text(self) -> str:
        if self.rechnung_nr == "":
            return ""
        return f"Nr. {self.rechnung_nr}"

    @property
    def directoryname_rechnung_verschickt(self) -> str:
        """
        2025-05-13 142.25 klangspielschweiz 2025-05-13_06-50-50_vesr20250528_01_R20250528_01.muller
        """
        v = f"{self.datum} {self.ftotal} klangspielschweiz {self.datum}_{self.zeit}_vesr{self.rechnung_nr}_R{self.rechnung_nr}.{self.lastname}"
        return v

    def replace(self, erhalten: bool, rechnung_nr: str) -> RechnungData:
        return dataclasses.replace(self, erhalten=erhalten, rechnung_nr=rechnung_nr)

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
            scale=2,
        )
        barcode.convert("1").save(filename_png)

    def xml_json_pdf(
        self,
        debug: bool,
        directory_top: pathlib.Path,
    ) -> None:
        directory = directory_top / self.directoryname_rechnung_verschickt
        directory.mkdir(parents=True, exist_ok=True)

        for filename_run in DIRECTORY_RUN_TEMPLATES.glob("*.sh"):
            filename_script = directory / filename_run.name
            shutil.copyfile(filename_run, filename_script)
            filename_script.chmod(filename_script.stat().st_mode | 0o111)

        filename_json = directory / ORIGINAL_JSON
        self.write_json(filename_json)

        self.json_pdf(debug=debug, filename_json=filename_json)

    def json_pdf(self, debug: bool, filename_json: pathlib.Path) -> None:
        filename_sonne_png = filename_json.with_name(FILENAME_SONNE_PNG.name)
        filename_sonne_png.write_bytes(FILENAME_SONNE_PNG.read_bytes())

        filename_datamatrix_png = filename_json.with_suffix(".png")
        self.write_datamatrix_png(filename_datamatrix_png)

        text_typ = util_jinja2.render(
            self,
            filename_datamatrix_png=filename_datamatrix_png,
            filename_sonne_png=filename_sonne_png,
        )

        filename_typst = filename_json.with_suffix(".typ")
        if debug:
            filename_typst.write_text(text_typ, encoding="utf-8")

        util_typst.render_pdf(
            text_typ=text_typ,
            filename_pdf=filename_typst.with_name(FILENAME_RECHNUNG_PDF),
        )

        filename_datamatrix_png.unlink(missing_ok=True)
        filename_sonne_png.unlink(missing_ok=True)

    @staticmethod
    def factory_json_pdf(debug: bool, directory_top: pathlib.Path) -> None:
        if not directory_top.is_dir():
            raise ValueError(f"Expected directory: {directory_top}")

        filename_json = directory_top / ORIGINAL_JSON
        if not filename_json.is_file():
            raise ValueError(f"Expected json file: {filename_json}")

        data = RechnungData.read_json(filename_json=filename_json)
        data.json_pdf(debug=debug, filename_json=filename_json)
