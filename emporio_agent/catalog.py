import csv
import functools
import json
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Literal, TypedDict

ProductCategory = Literal[
    "guitarras",
    "baixos",
    "baterias_percussao",
    "teclados_pianos",
    "violoes",
    "sopro_madeiras",
    "sopro_metais",
    "cordas_orquestrais",
    "ukuleles",
]
Availability = Literal["in_stock", "out_of_stock", "discontinued", "coming_soon"]
OrderStatus = Literal["pending", "confirmed", "shipped", "delivered", "cancelled"]
OrderLookupFailureReason = Literal["ambiguous_contact", "not_found"]


@dataclass(frozen=True, slots=True)
class Promotion:
    name: str
    discount_percent: int


class PriceQuote(TypedDict):
    list_price_brl: Decimal | None
    promotion: Promotion | None
    promotional_price_brl: Decimal | None
    pix_price_brl: Decimal | None
    pix_note: str | None
    best_cash_price_brl: Decimal | None
    max_installments: int | None
    installment_value_brl: Decimal | None
    installment_note: str | None
    installment_rule_note: str | None


@dataclass(frozen=True, slots=True)
class ProductSummary:
    product_id: int
    name: str
    category: ProductCategory
    availability: Availability
    list_price_brl: Decimal | None
    promotional_price_brl: Decimal | None
    discount_percent: int | None
    strings: str | None
    electronics: bool | None


@dataclass(frozen=True, slots=True)
class ProductDetail:
    product_id: int
    name: str
    category: ProductCategory
    availability: Availability
    description: str
    specs: dict[str, str]
    list_price_brl: Decimal | None
    promotion: Promotion | None
    promotional_price_brl: Decimal | None
    pix_price_brl: Decimal | None
    pix_note: str | None
    best_cash_price_brl: Decimal | None
    max_installments: int | None
    installment_value_brl: Decimal | None
    installment_note: str | None
    installment_rule_note: str | None


@dataclass(frozen=True, slots=True)
class ActivePromotion:
    product_id: int
    name: str
    list_price_brl: Decimal
    discount_percent: int
    promotional_price_brl: Decimal
    promotion_name: str
    availability: Availability


@dataclass(frozen=True, slots=True)
class StoreInfo:
    name: str
    slogan: str
    address: str
    phone: str
    whatsapp: str
    email: str
    opening_hours: dict[str, str]
    founded: int


@dataclass(frozen=True, slots=True)
class OrderItem:
    product_name: str
    quantity: int


class DeliveryWindows(TypedDict):
    received_on: date | None
    withdrawal_deadline: date | None
    withdrawal_window_open: bool | None
    defect_exchange_deadline: date | None
    defect_exchange_window_open: bool | None


@dataclass(frozen=True, slots=True)
class OrderDetail:
    found: Literal[True]
    order_id: int
    customer_first_name: str
    order_date: date
    status: OrderStatus
    status_label: str
    payment_method_label: str
    total_brl: Decimal
    items: tuple[OrderItem, ...]
    delivery_city: str
    tracking_code: str | None
    estimated_delivery: date | None
    estimated_delivery_has_passed: bool | None
    cancellation_reason: str | None
    received_on: date | None
    withdrawal_deadline: date | None
    withdrawal_window_open: bool | None
    defect_exchange_deadline: date | None
    defect_exchange_window_open: bool | None


@dataclass(frozen=True, slots=True)
class OrderLookupFailure:
    found: Literal[False]
    reason: OrderLookupFailureReason
    message: str


OrderStatusResult = OrderDetail | OrderLookupFailure

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
BRL_PREFIX = "R$ "
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
WITHDRAWAL_WINDOW_DAYS = 7
DEFECT_EXCHANGE_WINDOW_DAYS = 30
SETTLED_ORDER_STATUSES = frozenset({"delivered", "cancelled"})
SEARCH_STOPWORDS = frozenset({"de", "do", "da", "o", "a", "e", "com", "para"})
SEARCH_IGNORED_CHARACTERS = str.maketrans("", "", "-")
MIN_SEARCH_TOKEN_LENGTH = 2
PLURAL_SUFFIXES: dict[str, str] = {"oes": "ao", "s": ""}

PIX_NOTE_LIST_PRICE = "Preço à vista no PIX com 5% de desconto."
PIX_NOTE_PROMOTIONAL = (
    "O desconto de 5% do PIX não se aplica a preço promocional; "
    "à vista no PIX paga o preço promocional."
)
INSTALLMENT_NOTE = "sem juros no cartão de crédito"
INSTALLMENT_RULE_NOTE = (
    "até 12x sem juros no cartão; parcela mínima de R$ 80,00 de 4x a 6x e de R$ 100,00 de 7x a 12x"
)
NO_PRICE_QUOTE: PriceQuote = {
    "list_price_brl": None,
    "promotion": None,
    "promotional_price_brl": None,
    "pix_price_brl": None,
    "pix_note": None,
    "best_cash_price_brl": None,
    "max_installments": None,
    "installment_value_brl": None,
    "installment_note": None,
    "installment_rule_note": None,
}

CATEGORY_IDS: dict[ProductCategory, int] = {
    "guitarras": 1,
    "baixos": 2,
    "baterias_percussao": 3,
    "teclados_pianos": 4,
    "violoes": 5,
    "sopro_madeiras": 6,
    "sopro_metais": 7,
    "cordas_orquestrais": 8,
    "ukuleles": 9,
}
CATEGORY_SLUGS: dict[int, ProductCategory] = {
    category_id: category for category, category_id in CATEGORY_IDS.items()
}
UNPRICED_STATUSES = frozenset({"discontinued", "coming_soon"})
AVAILABILITY_BY_STATUS: dict[str, Availability] = {
    "discontinued": "discontinued",
    "coming_soon": "coming_soon",
}
SPEC_KEYS = (
    "top",
    "back_sides",
    "neck",
    "strings",
    "scale",
    "electronics",
    "color",
    "body",
    "keys",
    "polyphony",
    "shells",
    "pieces",
    "hardware",
    "type",
)
ELECTRONICS_FLAGS: dict[str, bool] = {"yes": True, "no": False}

ORDER_STATUS_LABELS: dict[OrderStatus, str] = {
    "pending": "pendente",
    "confirmed": "confirmado",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}
PAYMENT_METHOD_LABELS: dict[str, str] = {
    "pix": "PIX",
    "debit": "cartão de débito",
    "credit_3x": "cartão de crédito em 3x",
    "credit_6x": "cartão de crédito em 6x",
    "credit_12x": "cartão de crédito em 12x",
    "boleto": "boleto bancário",
}
NO_DELIVERY_WINDOWS: DeliveryWindows = {
    "received_on": None,
    "withdrawal_deadline": None,
    "withdrawal_window_open": None,
    "defect_exchange_deadline": None,
    "defect_exchange_window_open": None,
}
ORDER_NOT_FOUND = OrderLookupFailure(
    found=False,
    reason="not_found",
    message=(
        "Não localizei um pedido com esses dados. Peça ao cliente para conferir "
        "o número do pedido e o e-mail ou telefone cadastrado."
    ),
)
AMBIGUOUS_CONTACT = OrderLookupFailure(
    found=False,
    reason="ambiguous_contact",
    message="Mais de um cadastro usa esse e-mail. Peça o telefone cadastrado para confirmar.",
)

STORE_INFO = StoreInfo(
    name="Empório da Música",
    slogan="Sua música começa aqui",
    address="Rua 14 de Maio, 3200, Centro, Campo Grande - MS, CEP 79202-333",
    phone="(67) 3341-4444",
    whatsapp="(67) 3321-4500",
    email="contato@emporiodamusica.com.br",
    opening_hours={
        "segunda_a_sexta": "09:00 às 18:00",
        "sabado": "09:00 às 13:00",
        "domingo_e_feriados": "fechado",
    },
    founded=2008,
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
    description TEXT NOT NULL,
    search_text TEXT NOT NULL DEFAULT ''
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
POPULATE_SEARCH_TEXT_SQL = """
UPDATE products
SET search_text = normalize_search_text(
    products.name || ' ' || (
        SELECT categories.name FROM categories WHERE categories.category_id = products.category_id
    )
)
"""
CSV_TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    CATEGORIES_CSV: (INSERT_CATEGORY_SQL, CATEGORY_COLUMNS),
    PRODUCTS_CSV: (INSERT_PRODUCT_SQL, PRODUCT_COLUMNS),
    PROMOTIONS_CSV: (INSERT_PROMOTION_SQL, PROMOTION_COLUMNS),
    CUSTOMERS_CSV: (INSERT_CUSTOMER_SQL, CUSTOMER_COLUMNS),
    ORDERS_CSV: (INSERT_ORDER_SQL, ORDER_COLUMNS),
    ORDER_ITEMS_CSV: (INSERT_ORDER_ITEM_SQL, ORDER_ITEM_COLUMNS),
}

PRODUCT_BY_ID_SQL = """
SELECT products.product_id, products.name, products.category_id, products.price_cents,
       products.stock_quantity, products.status, products.specs, products.description,
       promotions.discount_percent, promotions.description AS promotion_name
FROM products
LEFT JOIN promotions
    ON promotions.product_id = products.product_id AND promotions.is_active = 1
WHERE products.product_id = ?
"""
SEARCH_PRODUCTS_SQL = """
SELECT products.product_id, products.name, products.category_id, products.price_cents,
       products.stock_quantity, products.status, products.specs, products.search_text,
       promotions.discount_percent, promotions.description AS promotion_name
FROM products
LEFT JOIN promotions
    ON promotions.product_id = products.product_id AND promotions.is_active = 1
WHERE (:category_id IS NULL OR products.category_id = :category_id)
  AND (:include_discontinued OR products.status != 'discontinued')
ORDER BY products.price_cents ASC, products.product_id ASC
"""
ACTIVE_PROMOTIONS_SQL = """
SELECT products.product_id, products.name, products.price_cents, products.stock_quantity,
       products.status, promotions.discount_percent, promotions.description AS promotion_name
FROM promotions
JOIN products ON products.product_id = promotions.product_id
WHERE promotions.is_active = 1
ORDER BY products.price_cents ASC, products.product_id ASC
"""
SHARED_EMAIL_COUNT_SQL = "SELECT count(*) FROM customers WHERE lower(trim(email)) = ?"
ORDER_BY_ID_AND_CONTACT_SQL = """
SELECT orders.order_id, orders.order_date, orders.status, orders.total_cents,
       orders.payment_method, orders.tracking_code, orders.estimated_delivery, orders.notes,
       customers.name AS customer_name, customers.city AS delivery_city
FROM orders
JOIN customers ON customers.customer_id = orders.customer_id
WHERE orders.order_id = ?
  AND (
    lower(trim(customers.email)) = ?
    OR replace(replace(replace(replace(customers.phone, '(', ''), ')', ''), '-', ''), ' ', '') = ?
  )
"""
ORDER_ITEMS_SQL = """
SELECT products.name AS product_name, order_items.quantity
FROM order_items
JOIN products ON products.product_id = order_items.product_id
WHERE order_items.order_id = ?
ORDER BY products.name ASC
"""


def singular_word(word: str) -> str:
    for suffix, replacement in PLURAL_SUFFIXES.items():
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            return word.removesuffix(suffix) + replacement
    return word


def normalize_search_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    simplified = stripped.lower().translate(SEARCH_IGNORED_CHARACTERS)
    return " ".join(singular_word(word) for word in simplified.split())


def load_catalog(data_dir: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.create_function(
        "normalize_search_text", 1, normalize_search_text, deterministic=True
    )
    connection.executescript(CREATE_TABLES_SQL)
    for csv_name, (insert_sql, columns) in CSV_TABLES.items():
        with (data_dir / csv_name).open(encoding="utf-8", newline="") as csv_file:
            records = csv.DictReader(csv_file)
            connection.executemany(
                insert_sql, ([record[column] for column in columns] for record in records)
            )
    connection.execute(POPULATE_SEARCH_TEXT_SQL)
    connection.commit()
    return connection


@functools.cache
def catalog_connection() -> sqlite3.Connection:
    return load_catalog(DATA_DIR)


def format_brl(value: Decimal) -> str:
    return BRL_PREFIX + format(value.quantize(CENTS), ",.2f").translate(BRL_SEPARATORS)


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
    has_promotion = promotion is not None
    cash_price = (
        promotional_price(list_price, promotion.discount_percent)
        if promotion is not None
        else pix_price(list_price)
    )
    max_installments, installment_value = installment_plan(
        cash_price if has_promotion else list_price
    )
    return {
        "list_price_brl": list_price,
        "promotion": promotion,
        "promotional_price_brl": cash_price if has_promotion else None,
        "pix_price_brl": None if has_promotion else cash_price,
        "pix_note": PIX_NOTE_PROMOTIONAL if has_promotion else PIX_NOTE_LIST_PRICE,
        "best_cash_price_brl": cash_price,
        "max_installments": max_installments,
        "installment_value_brl": installment_value,
        "installment_note": INSTALLMENT_NOTE,
        "installment_rule_note": INSTALLMENT_RULE_NOTE,
    }


def availability_of(status: str, stock_quantity: int) -> Availability:
    stock_availability: Availability = "in_stock" if stock_quantity > 0 else "out_of_stock"
    return AVAILABILITY_BY_STATUS.get(status, stock_availability)


def selected_specs(raw_specs: str) -> dict[str, str]:
    specs: dict[str, str] = json.loads(raw_specs)
    return {key: specs[key] for key in SPEC_KEYS if key in specs}


def promotion_from_row(row: sqlite3.Row) -> Promotion | None:
    if row["discount_percent"] is None:
        return None
    return Promotion(name=row["promotion_name"], discount_percent=row["discount_percent"])


def price_quote_from_row(row: sqlite3.Row) -> PriceQuote:
    if row["status"] in UNPRICED_STATUSES:
        return NO_PRICE_QUOTE
    return price_quote(brl_from_cents(row["price_cents"]), promotion_from_row(row))


def summary_from_row(row: sqlite3.Row) -> ProductSummary:
    quote = price_quote_from_row(row)
    promotion = quote["promotion"]
    specs = selected_specs(row["specs"])
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        category=CATEGORY_SLUGS[row["category_id"]],
        availability=availability_of(row["status"], row["stock_quantity"]),
        list_price_brl=quote["list_price_brl"],
        promotional_price_brl=quote["promotional_price_brl"],
        discount_percent=None if promotion is None else promotion.discount_percent,
        strings=specs.get("strings"),
        electronics=ELECTRONICS_FLAGS.get(specs.get("electronics", "")),
    )


def search_tokens(name_contains: str) -> list[str]:
    return [
        token
        for token in normalize_search_text(name_contains).split()
        if len(token) >= MIN_SEARCH_TOKEN_LENGTH and token not in SEARCH_STOPWORDS
    ]


def matches_every_token(search_text: str, tokens: list[str] | None) -> bool:
    if tokens is None:
        return True
    return bool(tokens) and all(token in search_text for token in tokens)


def category_id_of(category: ProductCategory | None) -> int | None:
    if category is None:
        return None
    return CATEGORY_IDS[category]


def search_products(
    name_contains: str | None,
    category: ProductCategory | None,
    min_price_brl: Decimal | None,
    max_price_brl: Decimal | None,
) -> list[ProductSummary]:
    tokens = None if name_contains is None else search_tokens(name_contains)
    parameters = {
        "category_id": category_id_of(category),
        "include_discontinued": tokens is not None,
    }
    rows = catalog_connection().execute(SEARCH_PRODUCTS_SQL, parameters).fetchall()
    summaries = [
        summary_from_row(row) for row in rows if matches_every_token(row["search_text"], tokens)
    ]
    return [
        summary
        for summary in summaries
        if within_price_range(summary, min_price_brl, max_price_brl)
    ]


def within_price_range(
    summary: ProductSummary, min_price_brl: Decimal | None, max_price_brl: Decimal | None
) -> bool:
    price = summary.promotional_price_brl or summary.list_price_brl
    if price is None:
        return min_price_brl is None and max_price_brl is None
    above_minimum = min_price_brl is None or price >= min_price_brl
    below_maximum = max_price_brl is None or price <= max_price_brl
    return above_minimum and below_maximum


def get_product(product_id: int) -> ProductDetail | None:
    row = catalog_connection().execute(PRODUCT_BY_ID_SQL, (product_id,)).fetchone()
    if row is None:
        return None
    return ProductDetail(
        product_id=row["product_id"],
        name=row["name"],
        category=CATEGORY_SLUGS[row["category_id"]],
        availability=availability_of(row["status"], row["stock_quantity"]),
        description=row["description"],
        specs=selected_specs(row["specs"]),
        **price_quote_from_row(row),
    )


def active_promotion_from_row(row: sqlite3.Row) -> ActivePromotion:
    list_price = brl_from_cents(row["price_cents"])
    return ActivePromotion(
        product_id=row["product_id"],
        name=row["name"],
        list_price_brl=list_price,
        discount_percent=row["discount_percent"],
        promotional_price_brl=promotional_price(list_price, row["discount_percent"]),
        promotion_name=row["promotion_name"],
        availability=availability_of(row["status"], row["stock_quantity"]),
    )


def list_active_promotions() -> list[ActivePromotion]:
    rows = catalog_connection().execute(ACTIVE_PROMOTIONS_SQL).fetchall()
    return [active_promotion_from_row(row) for row in rows]


def get_store_info() -> StoreInfo:
    return STORE_INFO


def normalized_email(customer_email: str | None) -> str | None:
    if customer_email is None:
        return None
    return customer_email.strip().lower()


def phone_digits(customer_phone: str | None) -> str | None:
    if customer_phone is None:
        return None
    return "".join(character for character in customer_phone if character.isdigit())


def email_is_shared(customer_email: str | None) -> bool:
    if customer_email is None:
        return False
    row = catalog_connection().execute(SHARED_EMAIL_COUNT_SQL, (customer_email,)).fetchone()
    customers_with_email: int = row[0]
    return customers_with_email > 1


def optional_date(raw_date: str | None) -> date | None:
    if raw_date is None:
        return None
    return date.fromisoformat(raw_date)


def has_passed(deadline: date | None, today: date) -> bool | None:
    if deadline is None:
        return None
    return today > deadline


def delivery_windows(row: sqlite3.Row, today: date) -> DeliveryWindows:
    received_on = optional_date(row["estimated_delivery"])
    if row["status"] != "delivered" or received_on is None:
        return NO_DELIVERY_WINDOWS
    withdrawal_deadline = received_on + timedelta(days=WITHDRAWAL_WINDOW_DAYS)
    order_date = date.fromisoformat(row["order_date"])
    defect_exchange_deadline = order_date + timedelta(days=DEFECT_EXCHANGE_WINDOW_DAYS)
    return {
        "received_on": received_on,
        "withdrawal_deadline": withdrawal_deadline,
        "withdrawal_window_open": today <= withdrawal_deadline,
        "defect_exchange_deadline": defect_exchange_deadline,
        "defect_exchange_window_open": today <= defect_exchange_deadline,
    }


def order_items_of(order_id: int) -> tuple[OrderItem, ...]:
    rows = catalog_connection().execute(ORDER_ITEMS_SQL, (order_id,)).fetchall()
    return tuple(
        OrderItem(product_name=row["product_name"], quantity=row["quantity"]) for row in rows
    )


def estimate_has_passed(row: sqlite3.Row, today: date) -> bool | None:
    if row["status"] in SETTLED_ORDER_STATUSES:
        return None
    return has_passed(optional_date(row["estimated_delivery"]), today)


def order_detail_from_row(row: sqlite3.Row, today: date) -> OrderDetail:
    status: OrderStatus = row["status"]
    return OrderDetail(
        found=True,
        order_id=row["order_id"],
        customer_first_name=row["customer_name"].split()[0],
        order_date=date.fromisoformat(row["order_date"]),
        status=status,
        status_label=ORDER_STATUS_LABELS[status],
        payment_method_label=PAYMENT_METHOD_LABELS[row["payment_method"]],
        total_brl=brl_from_cents(row["total_cents"]),
        items=order_items_of(row["order_id"]),
        delivery_city=row["delivery_city"],
        tracking_code=row["tracking_code"],
        estimated_delivery=optional_date(row["estimated_delivery"]),
        estimated_delivery_has_passed=estimate_has_passed(row, today),
        cancellation_reason=row["notes"] if status == "cancelled" else None,
        **delivery_windows(row, today),
    )


def get_order_status(
    order_id: int,
    customer_email: str | None,
    customer_phone: str | None,
    today: date,
) -> OrderStatusResult:
    if customer_email is None and customer_phone is None:
        raise ValueError("customer_email or customer_phone is required to look up an order")
    email = normalized_email(customer_email)
    phone = phone_digits(customer_phone)
    shared_email = email_is_shared(email)
    if shared_email and not phone:
        return AMBIGUOUS_CONTACT
    parameters = (order_id, None if shared_email else email, phone)
    row = catalog_connection().execute(ORDER_BY_ID_AND_CONTACT_SQL, parameters).fetchone()
    if row is None:
        return ORDER_NOT_FOUND
    return order_detail_from_row(row, today)
