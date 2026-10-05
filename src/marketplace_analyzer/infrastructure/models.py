"""SQLAlchemy 2.0 persistence models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from marketplace_analyzer.infrastructure.database import Base


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_sku: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    oem_number: Mapped[str | None] = mapped_column(String(120), index=True)
    name: Mapped[str] = mapped_column(String(500), index=True)
    barcode: Mapped[str | None] = mapped_column(String(80), index=True)
    brand: Mapped[str | None] = mapped_column(String(160), index=True)
    category: Mapped[str | None] = mapped_column(String(200), index=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    matches: Mapped[list["Match"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    __table_args__ = (UniqueConstraint("marketplace", "external_id", name="uq_listing_marketplace_external"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(40), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(700))
    url: Mapped[str | None] = mapped_column(Text)
    barcode: Mapped[str | None] = mapped_column(String(80), index=True)
    oem_number: Mapped[str | None] = mapped_column(String(120), index=True)
    brand: Mapped[str | None] = mapped_column(String(160))
    snapshots: Mapped[list["Snapshot"]] = relationship(back_populates="listing", cascade="all, delete-orphan")
    matches: Mapped[list["Match"]] = relationship(back_populates="listing", cascade="all, delete-orphan")


class Snapshot(Base):
    __tablename__ = "snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("marketplace_listings.id", ondelete="CASCADE"), index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    seller_count: Mapped[int | None] = mapped_column(Integer)
    review_count: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    favorite_count: Mapped[int | None] = mapped_column(Integer)
    sales_signal: Mapped[str | None] = mapped_column(String(120))
    listing: Mapped[MarketplaceListing] = relationship(back_populates="snapshots")


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("product_id", "listing_id", name="uq_match_product_listing"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("marketplace_listings.id", ondelete="CASCADE"), index=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    method: Mapped[str] = mapped_column(String(30))
    explainability: Mapped[str | None] = mapped_column(Text)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    product: Mapped[Product] = relationship(back_populates="matches")
    listing: Mapped[MarketplaceListing] = relationship(back_populates="matches")
