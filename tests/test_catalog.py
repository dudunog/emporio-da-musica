from emporio_agent.catalog import catalog_connection


def test_connection_is_created_once() -> None:
    assert catalog_connection() is catalog_connection()
