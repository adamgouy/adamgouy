"""Adapter pattern - legacy XML reports in a JSON dashboard.

Problems of the original code:
- the interfaces are incompatible: the legacy generator returns XML, the new dashboard reads JSON;
- the XML -> JSON conversion is rewritten in every function that needs a report (and it cheats:
  it rebuilds the JSON from the original dict instead of really converting the XML);
- the legacy generator is an external library: we cannot modify it;
- business code and format conversion are mixed, so everything is tightly coupled.

Solution: the dashboard code depends on one interface, `JSONReportSource`. The
`LegacyReportAdapter` implements that interface, keeps the legacy generator inside (composition)
and does the XML -> JSON conversion in ONE place. A future native JSON generator can implement the
same interface, and the business code will not change.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Given code (cannot be modified)
# ---------------------------------------------------------------------------

class LegacyReportGenerator:
    """Old reporting system from an external library: returns XML."""

    def generate_report(self, data: dict) -> str:
        xml = "<report>\n"
        for key, value in data.items():
            xml += f"  <{key}>{value}</{key}>\n"
        return xml + "</report>"


class AnalyticsDashboard:
    """New dashboard: only understands JSON."""

    def display(self, json_data: str) -> None:
        print("=== Analytics Dashboard ===")
        for key, value in json.loads(json_data).items():
            print(f"  {key}: {value}")


# ---------------------------------------------------------------------------
# Target interface + adapter
# ---------------------------------------------------------------------------

class JSONReportSource(ABC):
    """What the dashboard code expects: something that gives a report as a JSON string."""

    @abstractmethod
    def generate(self, data: dict) -> str: ...


class LegacyReportAdapter(JSONReportSource):
    def __init__(self, legacy_generator: LegacyReportGenerator):
        self._legacy = legacy_generator     # the adaptee is wrapped, not inherited

    def generate(self, data: dict) -> str:
        xml_report = self._legacy.generate_report(data)
        return json.dumps(self._xml_to_dict(xml_report))

    @classmethod
    def _xml_to_dict(cls, xml_report: str) -> dict:
        root = ET.fromstring(xml_report)
        return {element.tag: cls._typed(element.text) for element in root}

    @staticmethod
    def _typed(text: str | None):
        """XML only contains text: give numbers and booleans their real type back."""
        if text is None:
            return None
        text = text.strip()
        if text in ("True", "False"):
            return text == "True"
        for convert in (int, float):
            try:
                return convert(text)
            except ValueError:
                continue
        return text


class NativeJSONReportGenerator(JSONReportSource):
    """A modern generator: same interface, so it can replace the adapter with no other change."""

    def generate(self, data: dict) -> str:
        return json.dumps(data)


# ---------------------------------------------------------------------------
# Business code: only knows the interface
# ---------------------------------------------------------------------------

def show_sales_report(source: JSONReportSource, dashboard: AnalyticsDashboard) -> None:
    dashboard.display(source.generate({"total_sales": 150_000, "orders": 1234, "avg_order": 121.56}))


def show_inventory_report(source: JSONReportSource, dashboard: AnalyticsDashboard) -> None:
    dashboard.display(source.generate({"total_items": 5000, "low_stock": 45, "out_of_stock": 12}))


if __name__ == "__main__":
    dashboard = AnalyticsDashboard()
    legacy_source = LegacyReportAdapter(LegacyReportGenerator())
    show_sales_report(legacy_source, dashboard)
    show_inventory_report(legacy_source, dashboard)

    print("\nSame business code with the new generator:")
    show_sales_report(NativeJSONReportGenerator(), dashboard)
