import pytest
from sqlalchemy.ext.asyncio import create_async_engine


def test_database_driver_resolution():
    """Verify that SQLAlchemy resolves the appropriate async driver for supported URL schemes."""
    schemes = [
        ("sqlite+aiosqlite:///:memory:", "sqlite", "aiosqlite"),
        ("postgresql+psycopg://user:pass@localhost:5432/db", "postgresql", "psycopg"),
        ("postgresql+asyncpg://user:pass@localhost:5432/db", "postgresql", "asyncpg"),
        ("postgresql://user:pass@localhost:5432/db", "postgresql", "psycopg"),
    ]

    for url, expected_dialect, expected_driver in schemes:
        engine = create_async_engine(url)
        assert engine.dialect.name == expected_dialect, f"Failed for {url}: expected {expected_dialect}, got {engine.dialect.name}"
        assert engine.dialect.driver == expected_driver, f"Failed for {url}: expected {expected_driver}, got {engine.dialect.driver}"


def test_legacy_postgres_url_normalization():
    """Verify legacy postgres:// scheme normalization to postgresql://."""
    url = "postgres://user:pass@localhost:5432/db"
    if url.startswith("postgres://"):
        normalized = "postgresql://" + url[len("postgres://"):]
    engine = create_async_engine(normalized)
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "psycopg"
