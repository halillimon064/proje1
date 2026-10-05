"""Local dashboard and JSON API for imported supplier products."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from marketplace_analyzer.config import AppConfig, load_config
from marketplace_analyzer.importers.excel_importer import ExcelProductImporter
from marketplace_analyzer.infrastructure.database import Base, make_session_factory
from marketplace_analyzer.infrastructure.models import Product
from marketplace_analyzer.services.product_import_service import persist_products

WEB_ROOT = Path(__file__).parent


def create_app(config: AppConfig | None = None) -> FastAPI:
    """Build the dashboard with its dependencies supplied through configuration."""
    app_config = config or load_config()
    engine, session_factory = make_session_factory(
        app_config.database_url, app_config.data["database"].get("echo", False)
    )
    application = FastAPI(title="Pazaryeri Ürün Fırsat Analiz Sistemi", version="0.1.0")
    application.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=str(WEB_ROOT / "templates"))

    @application.on_event("startup")
    def create_schema() -> None:
        Base.metadata.create_all(engine)

    def get_session() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/products")
    def products_api(
        query: str | None = Query(default=None, max_length=200),
        brand: str | None = None,
        category: str | None = None,
        min_stock: int | None = Query(default=None, ge=0),
        session: Session = Depends(get_session),
    ) -> list[dict[str, object]]:
        records = session.scalars(_filtered_products(query, brand, category, min_stock)).all()
        return [_serialize_product(product) for product in records]

    @application.get("/")
    def dashboard(
        request: Request,
        query: str | None = None,
        brand: str | None = None,
        category: str | None = None,
        min_stock: int | None = Query(default=None, ge=0),
        imported: int | None = None,
        skipped: int | None = None,
        error: str | None = None,
        session: Session = Depends(get_session),
    ):
        products = session.scalars(_filtered_products(query, brand, category, min_stock)).all()
        brands = session.scalars(select(Product.brand).where(Product.brand.is_not(None)).distinct().order_by(Product.brand)).all()
        categories = session.scalars(select(Product.category).where(Product.category.is_not(None)).distinct().order_by(Product.category)).all()
        total = session.scalar(select(func.count(Product.id))) or 0
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "products": products,
                "brands": brands,
                "categories": categories,
                "total": total,
                "filters": {"query": query or "", "brand": brand or "", "category": category or "", "min_stock": min_stock},
                "notice": {"imported": imported, "skipped": skipped, "error": error},
            },
        )

    @application.post("/imports/excel")
    async def import_excel(
        workbook: UploadFile = File(...), session: Session = Depends(get_session)
    ) -> RedirectResponse:
        if not workbook.filename or not workbook.filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
            return RedirectResponse(url="/?error=Yalnızca+Excel+dosyası+yükleyebilirsiniz.", status_code=303)
        contents = await workbook.read()
        if not contents:
            return RedirectResponse(url="/?error=Boş+dosya+yüklenemez.", status_code=303)
        importer_settings = app_config.data["import"]
        importer = ExcelProductImporter(
            column_mapping=importer_settings["column_mapping"],
            required_columns=importer_settings["required_columns"],
            sheet_name=importer_settings["sheet_name"],
        )
        suffix = Path(workbook.filename).suffix
        try:
            with NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
                temporary.write(contents)
                temporary_path = Path(temporary.name)
            rows, report = importer.import_file(temporary_path)
            persist_products(session, rows)
        except ValueError as exc:
            return RedirectResponse(url=f"/?error={quote(str(exc))}", status_code=303)
        finally:
            if "temporary_path" in locals():
                temporary_path.unlink(missing_ok=True)
        return RedirectResponse(
            url=f"/?imported={report.imported_rows}&skipped={report.skipped_rows}", status_code=303
        )

    return application


def _filtered_products(
    query: str | None, brand: str | None, category: str | None, min_stock: int | None
) -> Select[tuple[Product]]:
    statement = select(Product).order_by(Product.updated_at.desc(), Product.id.desc())
    if query:
        search = f"%{query.strip()}%"
        statement = statement.where(Product.name.ilike(search) | Product.supplier_sku.ilike(search))
    if brand:
        statement = statement.where(Product.brand == brand)
    if category:
        statement = statement.where(Product.category == category)
    if min_stock is not None:
        statement = statement.where(Product.stock_quantity >= min_stock)
    return statement


def _serialize_product(product: Product) -> dict[str, object]:
    return {
        "id": product.id,
        "supplier_sku": product.supplier_sku,
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "purchase_price": str(product.purchase_price) if product.purchase_price is not None else None,
        "stock_quantity": product.stock_quantity,
    }


app = create_app()


def run() -> None:
    """Start the local development server."""
    import uvicorn

    uvicorn.run("marketplace_analyzer.web.app:app", host="127.0.0.1", port=8000, reload=True)
