import logging
import pathlib
import xml.etree.ElementTree as ET

from klangspiel_rechnung2026.util_dataclasses import (
    POSITION_TAG_RE,
    Position,
    RechnungData,
)

logger = logging.getLogger(__file__)


class XmlParser:
    @staticmethod
    def _position_sort_key(item: tuple[int, dict[str, str]]) -> int:
        return item[0]

    @staticmethod
    def _clean_value(value: str | None) -> str:
        if value is None:
            return ""
        return value.strip()

    @staticmethod
    def parse_positions(xml_values: dict[str, str]) -> list[Position]:
        positions_raw: dict[int, dict[str, str]] = {}
        for key, value in xml_values.items():
            match = POSITION_TAG_RE.match(key)
            if match is None:
                continue
            idx = int(match.group("idx"))
            field = match.group("field")
            fields = positions_raw.setdefault(idx, {})
            fields[field] = XmlParser._clean_value(value)

        positions: list[Position] = []
        for _idx, fields in sorted(
            positions_raw.items(),
            key=XmlParser._position_sort_key,
        ):
            positions.append(
                Position(
                    anzahl=fields["Anzahl"],
                    wo=fields["wo"],
                    unit=fields["Unit"],
                    text=fields["Text"],
                    preis=fields["Preis"],
                )
            )
        return positions

    @staticmethod
    def from_xml_values(xml_values: dict[str, str]) -> RechnungData:
        def _clean_value(value: str | None) -> str:
            if value is None:
                return ""
            return value.strip()

        try:
            return RechnungData(
                adresse=_clean_value(xml_values["adresse"]),
                telefon=_clean_value(xml_values["Telefon"]),
                email=_clean_value(xml_values["Email"]),
                bemerkungen=_clean_value(xml_values["Bemerkungen"]),
                za=_clean_value(xml_values["za"]),
                datum=_clean_value(xml_values["Datum"]),
                zeit=_clean_value(xml_values["Zeit"]),
                positionen=XmlParser.parse_positions(xml_values),
                gewicht_total=_clean_value(xml_values["GewichtTotal"]),
                versandkosten=_clean_value(xml_values["Versandkosten"]),
                versandkosten_eu=_clean_value(xml_values["VersandkostenEU"]),
                fTotal=_clean_value(xml_values["fTotal"]),
                g=_clean_value(xml_values["g"]),
            )
        except KeyError as e:
            logger.error(f"{e}: Valid keys are {sorted(xml_values.keys())}")
            raise e

    @staticmethod
    def _extract_xml_text(text: str) -> str:
        marker = "<?xml"
        start = text.find(marker)
        if start < 0:
            raise ValueError("No XML block found in input file")
        return text[start:]

    @staticmethod
    def _xml_to_flat_dict(xml_text: str) -> dict[str, str]:
        root = ET.fromstring(xml_text)
        if root.tag != "data":
            raise ValueError(f"Unexpected XML root tag: {root.tag!r}")

        values: dict[str, str] = {}
        for child in root:
            if child.tag is None:
                continue
            values[child.tag] = child.text or ""
        return values

    @classmethod
    def parse_file(cls, filename_xml: pathlib.Path) -> RechnungData:
        text = filename_xml.read_text(encoding="utf-8")
        xml_text = cls._extract_xml_text(text)
        xml_values = cls._xml_to_flat_dict(xml_text)
        data: RechnungData = cls.from_xml_values(xml_values)
        return data
