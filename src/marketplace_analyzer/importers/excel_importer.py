"""Resilient Excel importer with row-level Turkish error reporting."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd

from marketplace_analyzer.domain.ports import ProductImporter


@dataclass
class ImportReport:
    total_rows: int = 0
    imported_rows: int = 0
    skipped_rows: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)


class ExcelProductImporter(ProductImporter):
    def __init__(self, column_mapping: dict[str, str], required_columns: list[str], sheet_name: int | str = 0):
        self.column_mapping = column_mapping
        self.required_columns = set(required_columns)
        self.sheet_name = sheet_name

    def import_file(self, path: str | Path) -> tuple[list[dict[str, Any]], ImportReport]:
        source = Path(path)
        report = ImportReport()
        try:
            frame = pd.read_excel(source, sheet_name=self.sheet_name, dtype=object)
        except Exception as exc:
            raise ValueError(f"Excel dosyası okunamadı: {exc}") from exc
        headers = {str(header).strip().casefold(): header for header in frame.columns}
        resolved: dict[str, Any] = {}
        missing = []
        for field_name, expected_header in self.column_mapping.items():
            actual = headers.get(str(expected_header).strip().casefold())
            if actual is None and field_name in self.required_columns:
                missing.append(expected_header)
            elif actual is not None:
                resolved[field_name] = actual
        if missing:
            raise ValueError("Zorunlu sütunlar bulunamadı: " + ", ".join(missing))

        products = []
        report.total_rows = len(frame.index)
        for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
            item = {key: _clean(row[column]) for key, column in resolved.items()}
            try:
                for required in self.required_columns:
                    if item.get(required) is None:
                        raise ValueError(f"{self.column_mapping[required]} alanı boş.")
                if item.get("purchase_price") is not None:
                    item["purchase_price"] = _parse_decimal(item["purchase_price"], "Alış Fiyatı")
                if item.get("stock_quantity") is not None:
                    quantity = _parse_decimal(item["stock_quantity"], "Stok")
                    if quantity != quantity.to_integral_value() or quantity < 0:
                        raise ValueError("Stok negatif olmayan tam sayı olmalıdır.")
                    item["stock_quantity"] = int(quantity)
                products.append(item)
                report.imported_rows += 1
            except (ValueError, InvalidOperation) as exc:
                report.skipped_rows += 1
                report.errors.append({"row": row_number, "message": str(exc)})
        return products, report


def _clean(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _parse_decimal(value: Any, label: str) -> Decimal:
    normalized = str(value).strip().replace("₺", "").replace(" ", "")
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    else:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"{label} sayısal değil: {value}") from exc
