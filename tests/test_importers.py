import csv
from decimal import Decimal

import pandas as pd

from marketplace_analyzer.importers.excel_importer import ExcelProductImporter
from marketplace_analyzer.importers.manual_csv_importer import import_listings_csv


def test_excel_importer_keeps_valid_rows_and_reports_invalid_rows(tmp_path):
    path = tmp_path / "products.xlsx"
    pd.DataFrame([
        {"Ürün Kodu": "SKU-1", "Ürün Adı": "Filtre", "Alış Fiyatı": "1.234,50", "Stok": 3},
        {"Ürün Kodu": "", "Ürün Adı": "Eksik", "Alış Fiyatı": "bad", "Stok": 2},
    ]).to_excel(path, index=False)
    importer = ExcelProductImporter(
        {"supplier_sku": "Ürün Kodu", "name": "Ürün Adı", "purchase_price": "Alış Fiyatı", "stock_quantity": "Stok"},
        ["supplier_sku", "name"],
    )
    products, report = importer.import_file(path)
    assert products[0]["purchase_price"] == Decimal("1234.50")
    assert report.imported_rows == 1
    assert report.skipped_rows == 1
    assert report.errors[0]["row"] == 3


def test_manual_csv_importer_returns_listings_and_row_errors(tmp_path):
    path = tmp_path / "listings.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["marketplace", "external_id", "title", "price"])
        writer.writeheader()
        writer.writerow({"marketplace": "trendyol", "external_id": "42", "title": "Ürün", "price": "12,5"})
        writer.writerow({"marketplace": "", "external_id": "43", "title": "Eksik"})
    listings, errors = import_listings_csv(path)
    assert listings[0].price == Decimal("12.5")
    assert len(errors) == 1
