# Pazaryeri Ürün Fırsat Analiz Sistemi

Stage 1–2 foundation for importing wholesaler workbooks and normalizing marketplace data.

## Assumptions

- The initial database is SQLite for local development; `DATABASE_URL` selects Supabase/PostgreSQL in deployment.
- Excel columns are configurable in `settings.yaml`; workbook headers are matched case-insensitively after trimming.
- Invalid workbook rows are reported and skipped individually so valid rows still import.
- Marketplace collection is opt-in. Adapters expose barcode, OEM and keyword search, but no live endpoint is guessed or scraped. Configure compliant, documented endpoints before enabling network access.
- Manual CSV import is the reliable fallback. Source-specific CSV rows can be normalized to the common listing schema.
- No credentials are committed; `.env.example` documents required environment overrides.

## Setup

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Import an Excel workbook using `python -m marketplace_analyzer.cli import-excel path\to\supplier.xlsx`.
Run the test suite with `pytest`.

## Structure

See `src/marketplace_analyzer` for domain models, persistence, importers, and marketplace adapters. Stage 1 and 2 are foundations; matching, scoring, UI and deployment are later stages.
