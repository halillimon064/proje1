"""Command-line entry points."""

import argparse
import json
import logging

from marketplace_analyzer.config import load_config
from marketplace_analyzer.importers.excel_importer import ExcelProductImporter
from marketplace_analyzer.infrastructure.database import Base, make_session_factory
from marketplace_analyzer.services.product_import_service import persist_products


def main() -> None:
    parser = argparse.ArgumentParser(description="Pazaryeri ürün fırsat analiz sistemi")
    commands = parser.add_subparsers(dest="command", required=True)
    excel = commands.add_parser("import-excel", help="Toptancı Excel dosyasını doğrula ve içe aktar")
    excel.add_argument("path")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command == "import-excel":
        config = load_config()
        importer_config = config.data["import"]
        importer = ExcelProductImporter(**{key: importer_config[key] for key in ("column_mapping", "required_columns", "sheet_name")})
        rows, report = importer.import_file(args.path)
        engine, session_factory = make_session_factory(config.database_url, config.data["database"].get("echo", False))
        Base.metadata.create_all(engine)
        with session_factory() as session:
            persisted = persist_products(session, rows)
        print(json.dumps({"valid_rows": len(rows), "persisted_rows": persisted, "total_rows": report.total_rows,
                          "skipped_rows": report.skipped_rows, "errors": report.errors}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
