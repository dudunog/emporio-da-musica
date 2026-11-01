from dataclasses import asdict
from decimal import Decimal

from emporio_agent.catalog import (
    availability_of,
    catalog_connection,
    get_product,
)


def test_connection_is_created_once() -> None:
    assert catalog_connection() is catalog_connection()


def test_product_90_has_exclusive_discount_promotion() -> None:
    crafter = get_product(90)
    assert crafter is not None
    assert crafter.promotion is not None
    assert crafter.promotion.discount_percent == 18
    assert crafter.promotion.name == "Desconto Exclusivo"


def test_availability_of_maps_status_and_stock() -> None:
    assert availability_of("active", 0) == "out_of_stock"
    assert availability_of("active", 5) == "in_stock"
    assert availability_of("discontinued", 13) == "discontinued"
    assert availability_of("coming_soon", 2) == "coming_soon"


def test_active_product_without_stock_is_out_of_stock() -> None:
    giannini = get_product(96)
    assert giannini is not None
    assert giannini.availability == "out_of_stock"
    assert giannini.list_price_brl == Decimal("799.90")


def test_discontinued_product_has_no_sale_price() -> None:
    shelby = get_product(113)
    assert shelby is not None
    assert shelby.availability == "discontinued"
    assert shelby.list_price_brl is None
    assert shelby.pix_price_brl is None
    assert shelby.best_cash_price_brl is None
    assert shelby.max_installments is None
    assert shelby.installment_value_brl is None


def test_discontinued_product_with_stock_is_still_discontinued() -> None:
    ibanez = get_product(136)
    assert ibanez is not None
    assert ibanez.availability == "discontinued"
    assert "stock_quantity" not in asdict(ibanez)


def test_coming_soon_product_is_marked_coming_soon() -> None:
    kala = get_product(130)
    assert kala is not None
    assert kala.availability == "coming_soon"


def test_get_product_returns_none_for_unknown_id() -> None:
    assert get_product(999) is None
