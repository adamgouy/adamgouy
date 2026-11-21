"""Strategy pattern - multi-format report generator.

Answers to the questions about the original code:
1. To add XML or Markdown, you must edit TWO if/elif chains (in `generate_report` and in
   `save_report`) and not forget one of them.
2. It breaks the Open/Closed principle: the class must be modified for every new format.
3. It is hard to test: all the formats live in the same method, one format cannot be tested alone.
4. The format can only be chosen by passing a string; there is no clean way to switch it at runtime.
5. There is duplication: the format name is tested twice and the extension logic is repeated.

Solution: each format is a "strategy" class with the same interface (`format()` + `extension`).
`ReportGenerator` (the context) keeps a reference to one strategy and delegates the formatting
to it. Changing the format = giving it another strategy object, even while the program runs.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from html import escape
from pathlib import Path


class FormatStrategy(ABC):
    extension: str = ""

    @abstractmethod
    def format(self, data: list[dict]) -> str: ...


class PDFFormatStrategy(FormatStrategy):
    extension = "pdf"

    def format(self, data: list[dict]) -> str:
        border = "=" * 40
        rows = [f"| {item['name']:<20} | {item['value']:>12,} |" for item in data]
        return "\n".join(["PDF REPORT", border, *rows, border, "End of PDF report"])


class ExcelFormatStrategy(FormatStrategy):
    extension = "xlsx"

    def format(self, data: list[dict]) -> str:
        rows = [f"{item['name']}\t{item['value']}" for item in data]
        return "\n".join(["EXCEL REPORT", "Name\tValue", *rows])


class CSVFormatStrategy(FormatStrategy):
    extension = "csv"

    def format(self, data: list[dict]) -> str:
        return "\n".join(["name,value", *(f"{item['name']},{item['value']}" for item in data)])


class JSONFormatStrategy(FormatStrategy):
    extension = "json"

    def format(self, data: list[dict]) -> str:
        return json.dumps(data, indent=2)


# --- Final test of the exercise: new formats WITHOUT modifying any existing class ---

class HTMLFormatStrategy(FormatStrategy):
    extension = "html"

    def format(self, data: list[dict]) -> str:
        rows = "".join(
            f"\n    <tr><td>{escape(str(item['name']))}</td><td>{item['value']}</td></tr>" for item in data
        )
        return f"<table>\n    <tr><th>Name</th><th>Value</th></tr>{rows}\n</table>"


class MarkdownFormatStrategy(FormatStrategy):
    extension = "md"

    def format(self, data: list[dict]) -> str:
        rows = [f"| {item['name']} | {item['value']} |" for item in data]
        return "\n".join(["| Name | Value |", "|---|---:|", *rows])


class ReportGenerator:
    """The context: holds the data and delegates the formatting to the current strategy."""

    def __init__(self, data: list[dict], strategy: FormatStrategy | None = None):
        self.data = data
        self._strategy = strategy

    def set_strategy(self, strategy: FormatStrategy) -> None:
        self._strategy = strategy

    def generate_report(self) -> str:
        if self._strategy is None:
            raise ValueError("Choose a format first with set_strategy()")
        return self._strategy.format(self.data)

    def save_report(self, filename: str | Path) -> Path:
        content = self.generate_report()                      # also checks the strategy is set
        path = Path(filename).with_suffix("." + self._strategy.extension)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path


if __name__ == "__main__":
    sales = [
        {"name": "Sales Q1", "value": 15000},
        {"name": "Sales Q2", "value": 18000},
        {"name": "Sales Q3", "value": 22000},
        {"name": "Sales Q4", "value": 25000},
    ]
    generator = ReportGenerator(sales)
    for strategy in (PDFFormatStrategy(), CSVFormatStrategy(), JSONFormatStrategy(),
                     HTMLFormatStrategy(), MarkdownFormatStrategy()):
        generator.set_strategy(strategy)                      # switch format at runtime
        print(f"--- {type(strategy).__name__} ---")
        print(generator.generate_report(), "\n")

    generator.set_strategy(CSVFormatStrategy())
    print("Saved to", generator.save_report(Path(__file__).parent / "output" / "sales_report"))
