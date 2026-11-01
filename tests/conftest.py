import shutil
import sqlite3
from pathlib import Path

import pytest

from emporio_agent import catalog
from emporio_agent.catalog import CSV_TABLES, DATA_DIR, PRODUCTS_CSV, load_catalog

FIXTURES_DIR = Path(__file__).parent / "fixtures"
INJECTED_CATALOG_CSV = FIXTURES_DIR / "injected-catalog.csv"


@pytest.fixture
def injected_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> sqlite3.Connection:
    for csv_name in CSV_TABLES:
        source = INJECTED_CATALOG_CSV if csv_name == PRODUCTS_CSV else DATA_DIR / csv_name
        shutil.copy(source, tmp_path / csv_name)
    connection = load_catalog(tmp_path)
    monkeypatch.setattr(catalog, "catalog_connection", lambda: connection)
    return connection
