import csv
import functools
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CATEGORIES_CSV = "desafio_tecnico_ai_eng - categories.csv"
CUSTOMERS_CSV = "desafio_tecnico_ai_eng - customers.csv"
ORDERS_CSV = "desafio_tecnico_ai_eng - orders.csv"
ORDER_ITEMS_CSV = "desafio_tecnico_ai_eng - order_items.csv"
PRODUCTS_CSV = "desafio_tecnico_ai_eng - products.csv"
PROMOTIONS_CSV = "desafio_tecnico_ai_eng - promotions.csv"

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
