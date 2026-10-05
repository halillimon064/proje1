"""Marketplace-neutral data transfer objects."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class ListingData:
    marketplace: str
    external_id: str
    title: str
    url: str | None = None
    barcode: str | None = None
    oem_number: str | None = None
    brand: str | None = None
    price: Decimal | None = None
    seller_count: int | None = None
    review_count: int | None = None
    rating: Decimal | None = None


@dataclass(frozen=True)
class SnapshotData:
    listing_external_id: str
    captured_at: datetime
    price: Decimal | None = None
    seller_count: int | None = None
    review_count: int | None = None
    rating: Decimal | None = None
    favorite_count: int | None = None
    sales_signal: str | None = None
