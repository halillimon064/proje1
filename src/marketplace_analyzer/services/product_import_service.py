"""Application service for validating and persisting supplier products."""

from marketplace_analyzer.infrastructure.models import Product


def persist_products(session, rows: list[dict]) -> int:
    """Insert new products or update existing products by supplier SKU."""
    for row in rows:
        product = session.query(Product).filter_by(supplier_sku=row["supplier_sku"]).one_or_none()
        if product is None:
            session.add(Product(**row))
        else:
            for key, value in row.items():
                setattr(product, key, value)
    session.commit()
    return len(rows)
