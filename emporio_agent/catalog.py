import csv
import functools
import sqlite3
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Promotion:
    name: str
    discount_percent: int


@dataclass(frozen=True, slots=True)
class PriceQuote:
    list_price_brl: Decimal | None
    promotion: Promotion | None
    promotional_price_brl: Decimal | None
    pix_price_brl: Decimal | None
    pix_note: str | None
    best_cash_price_brl: Decimal | None
    max_installments: int | None
    installment_value_brl: Decimal | None
    installment_note: str | None


DATA_DIR = Path(__file__).parent.parent / "data"
CATEGORIES_CSV = "desafio_tecnico_ai_eng - categories.csv"
CUSTOMERS_CSV = "desafio_tecnico_ai_eng - customers.csv"
ORDERS_CSV = "desafio_tecnico_ai_eng - orders.csv"
ORDER_ITEMS_CSV = "desafio_tecnico_ai_eng - order_items.csv"
PRODUCTS_CSV = "desafio_tecnico_ai_eng - products.csv"
PROMOTIONS_CSV = "desafio_tecnico_ai_eng - promotions.csv"

CENTS = Decimal("0.01")
CENTS_PER_BRL = Decimal(100)
PERCENT = Decimal(100)
BRL_SEPARATORS = str.maketrans(",.", ".,")
PIX_DISCOUNT_PERCENT = 5
MAX_INSTALLMENTS = 12
MINIMUM_INSTALLMENT_BRL_UP_TO_3 = Decimal("50")
MINIMUM_INSTALLMENT_BRL_4_TO_6 = Decimal("80")
MINIMUM_INSTALLMENT_BRL_7_TO_12 = Decimal("100")
INSTALLMENT_MINIMUM_BRL: dict[int, Decimal] = {
    1: Decimal(0),
    **dict.fromkeys((2, 3), MINIMUM_INSTALLMENT_BRL_UP_TO_3),
    **dict.fromkeys((4, 5, 6), MINIMUM_INSTALLMENT_BRL_4_TO_6),
    **dict.fromkeys(range(7, MAX_INSTALLMENTS + 1), MINIMUM_INSTALLMENT_BRL_7_TO_12),
}

PIX_NOTE_LIST_PRICE = "Preço à vista no PIX com 5% de desconto."
PIX_NOTE_PROMOTIONAL = (
    "O desconto de 5% do PIX não se aplica a preço promocional; "
    "à vista no PIX paga o preço promocional."
)
INSTALLMENT_NOTE = "sem juros no cartão de crédito"
NO_PRICE_QUOTE = PriceQuote(
    list_price_brl=None,
    promotion=None,
    promotional_price_brl=None,
    pix_price_brl=None,
    pix_note=None,
    best_cash_price_brl=None,
    max_installments=None,
    installment_value_brl=None,
    installment_note=None,
)

CREATE_TABLES_SQL = """
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories (category_id),
    price_cents INTEGER NOT NULL,
    stock_quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    specs TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE promotions (
    promotion_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    discount_percent INTEGER NOT NULL,
    description TEXT NOT NULL,
    is_active INTEGER NOT NULL
);
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT NOT NULL
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    tracking_code TEXT,
    estimated_delivery TEXT,
    notes TEXT
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders (order_id),
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    quantity INTEGER NOT NULL
);
"""
INSERT_CATEGORY_SQL = "INSERT INTO categories (category_id, name, description) VALUES (?, ?, ?)"
CATEGORY_COLUMNS = ("category_id", "name", "description")
INSERT_PRODUCT_SQL = """
INSERT INTO products
    (product_id, name, category_id, price_cents, stock_quantity, status, specs, description)
VALUES (?, ?, ?, CAST(round(? * 100) AS INTEGER), ?, ?, ?, ?)
"""
PRODUCT_COLUMNS = (
    "product_id",
    "name",
    "category_id",
    "price_brl",
    "stock_quantity",
    "status",
    "specs",
    "description",
)
INSERT_PROMOTION_SQL = """
INSERT INTO promotions (promotion_id, product_id, discount_percent, description, is_active)
VALUES (?, ?, ?, ?, ?)
"""
PROMOTION_COLUMNS = ("promotion_id", "product_id", "discount_percent", "description", "is_active")
INSERT_CUSTOMER_SQL = """
INSERT INTO customers (customer_id, name, phone, email, city) VALUES (?, ?, ?, ?, ?)
"""
CUSTOMER_COLUMNS = ("customer_id", "name", "phone", "email", "city")
INSERT_ORDER_SQL = """
INSERT INTO orders
    (order_id, customer_id, order_date, status, total_cents, payment_method,
     tracking_code, estimated_delivery, notes)
VALUES (?, ?, ?, ?, CAST(round(? * 100) AS INTEGER), ?, NULLIF(?, ''), NULLIF(?, ''), NULLIF(?, ''))
"""
ORDER_COLUMNS = (
    "order_id",
    "customer_id",
    "order_date",
    "status",
    "total_brl",
    "payment_method",
    "tracking_code",
    "estimated_delivery",
    "notes",
)
INSERT_ORDER_ITEM_SQL = "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)"
ORDER_ITEM_COLUMNS = ("order_id", "product_id", "quantity")
CSV_TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    CATEGORIES_CSV: (INSERT_CATEGORY_SQL, CATEGORY_COLUMNS),
    PRODUCTS_CSV: (INSERT_PRODUCT_SQL, PRODUCT_COLUMNS),
    PROMOTIONS_CSV: (INSERT_PROMOTION_SQL, PROMOTION_COLUMNS),
    CUSTOMERS_CSV: (INSERT_CUSTOMER_SQL, CUSTOMER_COLUMNS),
    ORDERS_CSV: (INSERT_ORDER_SQL, ORDER_COLUMNS),
    ORDER_ITEMS_CSV: (INSERT_ORDER_ITEM_SQL, ORDER_ITEM_COLUMNS),
}


def load_catalog(data_dir: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(CREATE_TABLES_SQL)
    for csv_name, (insert_sql, columns) in CSV_TABLES.items():
        with (data_dir / csv_name).open(encoding="utf-8", newline="") as csv_file:
            records = csv.DictReader(csv_file)
            connection.executemany(
                insert_sql, ([record[column] for column in columns] for record in records)
            )
    connection.commit()
    return connection


@functools.cache
def catalog_connection() -> sqlite3.Connection:
    return load_catalog(DATA_DIR)


def format_brl(value: Decimal) -> str:
    return "R$ " + format(value.quantize(CENTS), ",.2f").translate(BRL_SEPARATORS)


def brl_from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / CENTS_PER_BRL).quantize(CENTS)


def pix_price(list_price: Decimal) -> Decimal:
    return promotional_price(list_price, PIX_DISCOUNT_PERCENT)


def promotional_price(list_price: Decimal, discount_percent: int) -> Decimal:
    discounted = list_price * (PERCENT - discount_percent) / PERCENT
    return discounted.quantize(CENTS, rounding=ROUND_HALF_UP)


def installment_plan(price: Decimal) -> tuple[int, Decimal]:
    allowed_counts = [
        count for count, minimum in INSTALLMENT_MINIMUM_BRL.items() if price >= minimum * count
    ]
    max_installments = max(allowed_counts)
    installment_value = (price / max_installments).quantize(CENTS, rounding=ROUND_HALF_UP)
    return max_installments, installment_value


def price_quote(list_price: Decimal, promotion: Promotion | None) -> PriceQuote:
    if promotion is None:
        cash_price = pix_price(list_price)
        max_installments, installment_value = installment_plan(list_price)
        return PriceQuote(
            list_price_brl=list_price,
            promotion=None,
            promotional_price_brl=None,
            pix_price_brl=cash_price,
            pix_note=PIX_NOTE_LIST_PRICE,
            best_cash_price_brl=cash_price,
            max_installments=max_installments,
            installment_value_brl=installment_value,
            installment_note=INSTALLMENT_NOTE,
        )
    cash_price = promotional_price(list_price, promotion.discount_percent)
    max_installments, installment_value = installment_plan(cash_price)
    return PriceQuote(
        list_price_brl=list_price,
        promotion=promotion,
        promotional_price_brl=cash_price,
        pix_price_brl=None,
        pix_note=PIX_NOTE_PROMOTIONAL,
        best_cash_price_brl=cash_price,
        max_installments=max_installments,
        installment_value_brl=installment_value,
        installment_note=INSTALLMENT_NOTE,
    )
