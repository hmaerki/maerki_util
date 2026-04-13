import logging
import pathlib
import xml.etree.ElementTree as ET

from .util_dataclasses import Position, RechnungData

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
    def from_xml_values(xml_values: dict[str, str]) -> RechnungData:
        def _clean_value(value: str | None) -> str:
            assert value is not None
            if value is None:
                return ""
            return value.strip()

        try:

            class X:
                def __init__(self, xml_values: dict[str, str]) -> None:
                    self.positionen: list[Position] = []
                    ipos = 0
                    while True:
                        ipos += 1

                        def get_pos(ipos: int, tag: str, optional=False) -> str:
                            try:
                                return xml_values[f"Pos{ipos}{tag}"]
                            except KeyError:
                                if optional:
                                    return ""
                                raise

                        try:
                            self.positionen.append(
                                Position(
                                    anzahl=get_pos(ipos, "Anzahl"),
                                    wo=get_pos(ipos, "wo", optional=True),
                                    unit=get_pos(ipos, "Unit", optional=True),
                                    text=get_pos(ipos, "Text"),
                                    preis=get_pos(ipos, "Preis"),
                                )
                            )
                        except KeyError:
                            break
                    self.kwargs = {
                        k.lower(): _clean_value(xml_values[k])
                        for k in sorted(xml_values.keys())
                        if (not k.startswith("Pos")) and (k != "links")
                    }

            x = X(xml_values)

            return RechnungData(
                positionen=x.positionen,
                **x.kwargs,
            )
        except KeyError as e:
            logger.error(f"{e}: Valid keys are {sorted(xml_values.keys())}")
            raise e

    @staticmethod
    def _extract_xml_text(text: str) -> str:
        marker = "<?xml"
        start = text.find(marker)
        if start < 0:
            raise ValueError(f"No XML block found in: {text}")
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
    def parse_text(cls, raw_text: str) -> RechnungData:
        xml_text = cls._extract_xml_text(raw_text)
        xml_values = cls._xml_to_flat_dict(xml_text)
        data: RechnungData = cls.from_xml_values(xml_values)
        return data

    @classmethod
    def parse_file(cls, filename_xml: pathlib.Path) -> RechnungData:
        raw_text = filename_xml.read_text(encoding="utf-8")
        return cls.parse_text(raw_text=raw_text)
