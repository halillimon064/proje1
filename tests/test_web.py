from pathlib import Path

from fastapi.testclient import TestClient

from marketplace_analyzer.config import AppConfig
from marketplace_analyzer.web.app import create_app


def test_dashboard_and_health_are_available(tmp_path: Path):
    config = AppConfig({
        "database": {"url": f"sqlite:///{tmp_path / 'dashboard.db'}", "echo": False},
        "import": {"column_mapping": {}, "required_columns": [], "sheet_name": 0},
    })
    with TestClient(create_app(config)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/")
        assert response.status_code == 200
        assert "Ürün Fırsat Analizi" in response.text
