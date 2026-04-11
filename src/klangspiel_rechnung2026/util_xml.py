import pathlib
import xml.etree.ElementTree as ET

from klangspiel_rechnung2026.util_dataclasses import RechnungData, from_xml_values


class XmlParser:
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
        data: RechnungData = from_xml_values(xml_values)
        return data
