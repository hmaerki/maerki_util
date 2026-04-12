import pathlib
import xml.etree.ElementTree as ET

from klangspiel_rechnung2026.util_dataclasses import RechnungData, parse_positions


class XmlParser:
    @staticmethod
    def from_xml_values(xml_values: dict[str, str]) -> RechnungData:
        def _clean_value(value: str | None) -> str:
            if value is None:
                return ""
            return value.strip()

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
