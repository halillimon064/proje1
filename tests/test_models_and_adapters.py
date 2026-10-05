from marketplace_analyzer.infrastructure.database import Base, make_session_factory
from marketplace_analyzer.infrastructure import models  # noqa: F401
from marketplace_analyzer.marketplaces.adapters import TrendyolAdapter


def test_models_create_sqlite_schema_and_relations(tmp_path):
    engine, factory = make_session_factory(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with factory() as session:
        assert session.query(models.Product).count() == 0


def test_marketplace_adapter_requires_explicit_endpoint():
    adapter = TrendyolAdapter(base_url="", user_agents=["test-agent"])
    try:
        adapter.search_keyword("filtre")
    except RuntimeError as exc:
        assert "endpoint" in str(exc)
    else:
        raise AssertionError("Adapter must not guess an endpoint")
