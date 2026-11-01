from dataclasses import asdict
from datetime import date
from decimal import Decimal

from emporio_agent.catalog import (
    ACTIVE_PROMOTIONS_SQL,
    PRODUCT_BY_ID_SQL,
    SEARCH_PRODUCTS_SQL,
    availability_of,
    catalog_connection,
    get_order_status,
    get_product,
    list_active_promotions,
    search_products,
)
from emporio_agent.tools import dispatch_tool

TODAY = date(2026, 11, 1)
CONTACT_FIELDS = {"phone", "email", "customer_id", "city", "address", "customer_email"}
SQL_INJECTION_QUERY = "Violões'; DROP TABLE products; --"


def test_connection_is_created_once() -> None:
    assert catalog_connection() is catalog_connection()


def test_search_violoes_up_to_1000_matches_catalog() -> None:
    summaries = search_products(None, "violoes", None, Decimal("1000"))
    product_ids = [summary.product_id for summary in summaries]
    assert len(product_ids) == 13
    assert 96 in product_ids
    assert 113 not in product_ids
    availability_by_id = {summary.product_id: summary.availability for summary in summaries}
    assert availability_by_id[96] == "out_of_stock"
    prices = [summary.list_price_brl for summary in summaries]
    assert all(price is not None and price <= Decimal("1000") for price in prices)
    assert prices == sorted(prices, key=lambda price: price or Decimal(0))


def test_search_price_limits_are_inclusive() -> None:
    product_ids = [
        summary.product_id for summary in search_products(None, "violoes", None, Decimal("999"))
    ]
    assert 112 in product_ids
    assert 101 not in product_ids
    from_999 = [
        summary.product_id for summary in search_products(None, "violoes", Decimal("999"), None)
    ]
    assert 112 in from_999
    assert 91 not in from_999


def test_search_empty_categories_return_empty_lists() -> None:
    assert search_products(None, "sopro_madeiras", None, None) == []
    assert search_products(None, "sopro_metais", None, None) == []
    assert search_products(None, "cordas_orquestrais", None, None) == []
    assert search_products(None, "teclados_pianos", None, Decimal("500")) == []


def test_search_min_above_max_returns_empty_list() -> None:
    assert search_products(None, "violoes", Decimal("2000"), Decimal("1000")) == []


def test_search_without_filters_returns_every_product_except_discontinued() -> None:
    summaries = search_products(None, None, None, None)
    assert len(summaries) == 63
    assert all(summary.availability != "discontinued" for summary in summaries)


def test_search_query_matches_name_case_insensitively() -> None:
    summaries = search_products("takamine gd20", None, None, None)
    assert [summary.product_id for summary in summaries] == [95]
    assert summaries[0].strings == "steel"
    assert summaries[0].electronics is False


def test_search_matches_every_token_ignoring_accents_order_and_stopwords() -> None:
    assert [
        summary.product_id for summary in search_products("Yamaha F310 violão", None, None, None)
    ] == [87]
    yamaha_violoes = search_products("violão Yamaha", None, None, None)
    assert {summary.product_id for summary in yamaha_violoes} == {81, 82, 87, 92, 98, 104, 114}
    seven_strings = search_products("Shelby SN-7C de 7 cordas", None, None, None)
    assert [summary.product_id for summary in seven_strings] == [113]
    violoes = search_products("violao", None, None, None)
    assert len(violoes) == 35
    assert all(summary.category == "violoes" for summary in violoes)
    assert search_products("Fender Jazz Bass", None, None, None) == []
    assert search_products("Fender", None, None, None) != []


def test_search_treats_like_wildcards_as_literal_characters() -> None:
    assert search_products("%", None, None, None) == []
    assert search_products("_", None, None, None) == []
    assert search_products("%%", None, None, None) == []
    assert search_products("F3_0", None, None, None) == []
    assert search_products("de", None, None, None) == []


def test_search_query_includes_discontinued_without_price() -> None:
    summaries = search_products("Shelby SN-7C", None, None, None)
    assert [summary.product_id for summary in summaries] == [113]
    assert summaries[0].availability == "discontinued"
    assert summaries[0].list_price_brl is None
    assert summaries[0].promotional_price_brl is None


def test_search_by_category_excludes_discontinued_but_marks_coming_soon() -> None:
    ukuleles = {
        summary.product_id: summary for summary in search_products(None, "ukuleles", None, None)
    }
    assert ukuleles[130].availability == "coming_soon"
    bass_ids = [summary.product_id for summary in search_products(None, "baixos", None, None)]
    assert 136 not in bass_ids
    assert bass_ids == [138, 135, 137]


def test_search_products_rejects_sql_in_arguments() -> None:
    assert search_products(SQL_INJECTION_QUERY, None, None, None) == []
    arguments: dict[str, object] = {
        "name_contains": None,
        "category": SQL_INJECTION_QUERY,
        "min_price_brl": None,
        "max_price_brl": None,
    }
    tool_result = dispatch_tool("search_products", arguments, TODAY)
    assert tool_result.is_error is True
    assert "category" in tool_result.content
    assert catalog_connection().execute("SELECT count(*) FROM products").fetchone()[0] == 65


def test_list_active_promotions_returns_exactly_the_four_active() -> None:
    promotions = list_active_promotions()
    assert [promotion.product_id for promotion in promotions] == [127, 121, 90, 94]
    assert [promotion.promotional_price_brl for promotion in promotions] == [
        Decimal("323.10"),
        Decimal("439.20"),
        Decimal("1967.18"),
        Decimal("5519.08"),
    ]
    assert [promotion.discount_percent for promotion in promotions] == [10, 20, 18, 8]
    assert all(promotion.availability == "in_stock" for promotion in promotions)


def test_promotion_filter_lives_in_sql_not_in_python() -> None:
    assert "is_active = 1" in ACTIVE_PROMOTIONS_SQL
    assert "is_active = 1" in PRODUCT_BY_ID_SQL
    assert "is_active = 1" in SEARCH_PRODUCTS_SQL
    takamine = get_product(95)
    giannini = get_product(96)
    martin = get_product(93)
    assert takamine is not None and takamine.promotion is None
    assert giannini is not None and giannini.promotion is None
    assert martin is not None and martin.promotion is None
    assert "Oferta Especial" not in str(asdict(takamine))


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


def test_get_product_selects_known_specs_only() -> None:
    takamine = get_product(95)
    assert takamine is not None
    assert takamine.specs == {
        "top": "Cedro Sólido",
        "back_sides": "Sapele",
        "neck": "Mogno",
        "strings": "steel",
        "scale": "650mm",
        "electronics": "no",
        "color": "Natural",
    }
    assert takamine.category == "violoes"
    fender = search_products("Stratocaster", None, None, None)[0]
    assert fender.electronics is None
    assert fender.strings == "6"


def test_order_status_hides_customer_contact() -> None:
    order = get_order_status(8, "anacarol.ferreira@coldmail.com", None, TODAY)
    payload = asdict(order)
    assert payload["found"] is True
    assert not CONTACT_FIELDS & set(payload)
    assert payload["delivery_city"] == "Campo Grande"
    assert payload["customer_first_name"] == "Ana"


def test_sql_injection_strings_leave_tables_intact() -> None:
    assert get_order_status(8, "' OR 1=1 --", None, TODAY) == get_order_status(
        999, "nobody@example.com", None, TODAY
    )
    arguments: dict[str, object] = {
        "order_id": "8; DROP TABLE orders",
        "customer_email": "x",
        "customer_phone": None,
    }
    assert dispatch_tool("get_order_status", arguments, TODAY).is_error is True
    assert catalog_connection().execute("SELECT count(*) FROM orders").fetchone()[0] == 20
    assert catalog_connection().execute("SELECT count(*) FROM products").fetchone()[0] == 65
