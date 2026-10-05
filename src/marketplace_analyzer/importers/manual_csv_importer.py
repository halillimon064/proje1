"""Manual marketplace CSV fallback using the normalized listing schema."""

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from marketplace_analyzer.domain.entities import ListingData

REQUIRED_HEADERS = {"marketplace", "external_id", "title"}


def import_listings_csv(path: str | Path) -> tuple[list[ListingData], list[dict[str, object]]]:
    listings: list[ListingData] = []
    errors: list[dict[str, object]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = {header.strip() for header in (reader.fieldnames or [])}
        missing = REQUIRED_HEADERS - headers
        if missing:
            raise ValueError("CSV zorunlu sütunları eksik: " + ", ".join(sorted(missing)))
        for row_number, row in enumerate(reader, start=2):
            try:
                def optional_decimal(key: str) -> Decimal | None:
                    raw = (row.get(key) or "").strip()
                    return Decimal(raw.replace(",", ".")) if raw else None
                def optional_int(key: str) -> int | None:
                    raw = (row.get(key) or "").strip()
                    return int(raw) if raw else None
                marketplace, external_id, title = tuple((row.get(k) or "").strip() for k in ("marketplace", "external_id", "title"))
                if not all((marketplace, external_id, title)):
                    raise ValueError("Pazaryeri, ürün kimliği ve başlık boş olamaz.")
                listings.append(ListingData(
                    marketplace=marketplace, external_id=external_id, title=title,
                    url=(row.get("url") or "").strip() or None,
                    barcode=(row.get("barcode") or "").strip() or None,
                    oem_number=(row.get("oem_number") or "").strip() or None,
                    brand=(row.get("brand") or "").strip() or None,
                    price=optional_decimal("price"), seller_count=optional_int("seller_count"),
                    review_count=optional_int("review_count"), rating=optional_decimal("rating"),
                ))
            except (ValueError, InvalidOperation) as exc:
                errors.append({"row": row_number, "message": str(exc)})
    return listings, errors
