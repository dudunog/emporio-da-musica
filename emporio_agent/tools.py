import json
import logging
from collections.abc import Callable, Collection
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from typing import TypedDict

from emporio_agent.catalog import (
    CATEGORY_IDS,
    format_brl,
    get_order_status,
    get_product,
    get_store_info,
    list_active_promotions,
    search_products,
)
from emporio_agent.policies import POLICY_TOPICS, get_policy

LOGGER = logging.getLogger(__name__)
BRAZILIAN_DATE_FORMAT = "%d/%m/%Y"
LABEL_SUFFIX = "_label"

SEARCH_PRODUCTS_TOOL = "search_products"
GET_PRODUCT_TOOL = "get_product"
GET_ORDER_STATUS_TOOL = "get_order_status"
LIST_ACTIVE_PROMOTIONS_TOOL = "list_active_promotions"
GET_STORE_INFO_TOOL = "get_store_info"
GET_POLICY_TOOL = "get_policy"


class ToolDefinition(TypedDict):
    name: str
    description: str
    strict: bool
    input_schema: dict[str, object]


OPTIONAL_STRING_SCHEMA: dict[str, object] = {"type": ["string", "null"]}
OPTIONAL_NUMBER_SCHEMA: dict[str, object] = {"type": ["number", "null"]}
TOOL_DEFINITIONS: list[ToolDefinition] = [
    {
        "name": SEARCH_PRODUCTS_TOOL,
        "description": (
            "Search the catalog by product name, category and/or list-price range in BRL (at "
            "least one filter); the product_id used by get_product comes from these results. "
            "name_contains is matched word by word, ignoring accents, case and hyphens, against "
            "the product name plus its category name, so pass only the brand and the model code "
            "('Takamine GD20', 'F310'), never a whole sentence; when it returns nothing, retry "
            "with fewer words before concluding the product does not exist. When the customer "
            "names only an instrument type (saxofone, violino, bateria), search by category "
            "instead of by name; each result already carries availability, list price, "
            "promotional price, discount percent and string type, enough for a plain price, "
            "stock or options question. With name_contains, discontinued and coming-soon "
            "products are included so their status can be explained; with category or price "
            "only, discontinued products are omitted but out-of-stock ones still appear marked."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "name_contains": {
                    **OPTIONAL_STRING_SCHEMA,
                    "description": (
                        "Brand and model code from the product name, such as 'Takamine GD20' "
                        "or 'SN-7C'; no sentences and no generic words."
                    ),
                },
                "category": {
                    "type": ["string", "null"],
                    "enum": [*CATEGORY_IDS, None],
                    "description": (
                        "Catalog category slug: violão = violoes; ukulele = ukuleles; guitarra = "
                        "guitarras; baixo = baixos; teclado, piano, sintetizador, controlador = "
                        "teclados_pianos; bateria, percussão = baterias_percussao; saxofone, "
                        "clarinete, flauta, oboé = sopro_madeiras; trompete, trombone, tuba, "
                        "trompa = sopro_metais; violino, viola, violoncelo, contrabaixo acústico "
                        "= cordas_orquestrais."
                    ),
                },
                "min_price_brl": {
                    **OPTIONAL_NUMBER_SCHEMA,
                    "description": "Minimum list price in BRL, inclusive.",
                },
                "max_price_brl": {
                    **OPTIONAL_NUMBER_SCHEMA,
                    "description": "Maximum list price in BRL, inclusive.",
                },
            },
            "required": ["name_contains", "category", "min_price_brl", "max_price_brl"],
            "additionalProperties": False,
        },
    },
    {
        "name": GET_PRODUCT_TOOL,
        "description": (
            "Return the full details of one product by product_id, taken from a search_products "
            "result: description, selected specs, availability, list price, active promotion, "
            "PIX price with its note, best cash price, installment plan and the installment "
            "rule with its minimum amounts, all amounts already formatted in BRL. Call it when "
            "the customer asks for PIX price, installments, "
            "promotion details, description or specs; a plain price or stock question is already "
            "answered by search_products. Discontinued products come without prices. Returns "
            "null when the product_id does not exist."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer", "description": "Catalog product_id."},
            },
            "required": ["product_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": GET_ORDER_STATUS_TOOL,
        "description": (
            "Look up one order by order_id plus the customer's registered e-mail or phone; call "
            "it only after the customer gave the order number and at least one of the two "
            "contacts. Returns status_label and payment_method_label in Portuguese, items, total "
            "paid, tracking_code, estimated_delivery with estimated_delivery_has_passed (null "
            "once delivered or cancelled) and, for delivered orders, the withdrawal and "
            "defect-exchange deadlines with whether each window is still open, all computed for "
            "today; every date also comes as a *_label field in dd/mm/yyyy, which is the form to "
            "quote. When found is false, reason is not_found (order number or contact do not "
            "match: ask the customer to check both, never say which one failed) or "
            "ambiguous_contact (the e-mail belongs to more than one customer: ask for the "
            "registered phone and call again with it). For delivered orders received_on is the "
            "delivery date on record and prevails over the date the customer states."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer", "description": "Order number."},
                "customer_email": {
                    **OPTIONAL_STRING_SCHEMA,
                    "description": "E-mail registered by the customer, if provided.",
                },
                "customer_phone": {
                    **OPTIONAL_STRING_SCHEMA,
                    "description": "Phone registered by the customer, if provided.",
                },
            },
            "required": ["order_id", "customer_email", "customer_phone"],
            "additionalProperties": False,
        },
    },
    {
        "name": LIST_ACTIVE_PROMOTIONS_TOOL,
        "description": (
            "List every promotion currently active, with product, list price, discount percent "
            "and promotional price already formatted. Use it for questions about current "
            "promotions or discounts; promotions absent from this list are not valid."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": GET_STORE_INFO_TOOL,
        "description": (
            "Return the store's address, landline phone, WhatsApp, e-mail, opening hours per day "
            "and company data. Use it for address, contact and hours questions and whenever the "
            "customer asks to talk to a person."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": GET_POLICY_TOOL,
        "description": (
            "Return one section of the store policy manual by topic. Use it for questions about "
            "payment and installments, exchanges and returns, shipping, promotion rules, customer "
            "service, warranty or privacy, and answer only the relevant part. A defect or "
            "warranty question may need both exchanges_returns and warranty; regular opening "
            "hours come from get_store_info."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": [*POLICY_TOPICS],
                    "description": "Policy section to read.",
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
    },
]


@dataclass(frozen=True, slots=True)
class ToolResult:
    content: str
    is_error: bool


def required_int(arguments: dict[str, object], name: str) -> int:
    value = arguments.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Argument '{name}' must be an integer, got {value!r}.")
    return value


def optional_string(arguments: dict[str, object], name: str) -> str | None:
    value = arguments.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Argument '{name}' must be a string or null, got {value!r}.")
    return value


def optional_decimal(arguments: dict[str, object], name: str) -> Decimal | None:
    value = arguments.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"Argument '{name}' must be a number or null, got {value!r}.")
    return Decimal(str(value))


def required_choice[Choice: str](
    arguments: dict[str, object], name: str, choices: Collection[Choice]
) -> Choice:
    value = arguments.get(name)
    matches = [choice for choice in choices if choice == value]
    if not matches:
        raise ValueError(f"Argument '{name}' must be one of {sorted(choices)}, got {value!r}.")
    return matches[0]


def optional_choice[Choice: str](
    arguments: dict[str, object], name: str, choices: Collection[Choice]
) -> Choice | None:
    if arguments.get(name) is None:
        return None
    return required_choice(arguments, name, choices)


def serialize_nested(value: object) -> object:
    if isinstance(value, dict):
        return serialize_payload(value)
    if isinstance(value, tuple):
        return [serialize_nested(entry) for entry in value]
    return value


def serialize_field(name: str, value: object) -> dict[str, object]:
    if isinstance(value, Decimal):
        return {name: format_brl(value)}
    if isinstance(value, date):
        return {name: value.isoformat(), name + LABEL_SUFFIX: value.strftime(BRAZILIAN_DATE_FORMAT)}
    return {name: serialize_nested(value)}


def serialize_payload(payload: dict[str, object]) -> dict[str, object]:
    serialized: dict[str, object] = {}
    for name, value in payload.items():
        serialized.update(serialize_field(name, value))
    return serialized


def dump_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False)


def run_search_products(arguments: dict[str, object], _today: date) -> str:
    name_contains = optional_string(arguments, "name_contains")
    category = optional_choice(arguments, "category", CATEGORY_IDS)
    min_price_brl = optional_decimal(arguments, "min_price_brl")
    max_price_brl = optional_decimal(arguments, "max_price_brl")
    search_filters = (name_contains, category, min_price_brl, max_price_brl)
    if all(search_filter is None for search_filter in search_filters):
        raise ValueError(
            "search_products requires at least one filter (name_contains, category or price)."
        )
    summaries = search_products(name_contains, category, min_price_brl, max_price_brl)
    return dump_json([serialize_payload(asdict(summary)) for summary in summaries])


def run_get_product(arguments: dict[str, object], _today: date) -> str:
    product = get_product(required_int(arguments, "product_id"))
    if product is None:
        return dump_json(None)
    return dump_json(serialize_payload(asdict(product)))


def run_get_order_status(arguments: dict[str, object], today: date) -> str:
    order_status = get_order_status(
        order_id=required_int(arguments, "order_id"),
        customer_email=optional_string(arguments, "customer_email"),
        customer_phone=optional_string(arguments, "customer_phone"),
        today=today,
    )
    return dump_json(serialize_payload(asdict(order_status)))


def run_list_active_promotions(_arguments: dict[str, object], _today: date) -> str:
    return dump_json(
        [serialize_payload(asdict(promotion)) for promotion in list_active_promotions()]
    )


def run_get_store_info(_arguments: dict[str, object], _today: date) -> str:
    return dump_json(serialize_payload(asdict(get_store_info())))


def run_get_policy(arguments: dict[str, object], _today: date) -> str:
    topic = required_choice(arguments, "topic", POLICY_TOPICS)
    return dump_json({"topic": topic, "title": POLICY_TOPICS[topic], "text": get_policy(topic)})


TOOL_HANDLERS: dict[str, Callable[[dict[str, object], date], str]] = {
    SEARCH_PRODUCTS_TOOL: run_search_products,
    GET_PRODUCT_TOOL: run_get_product,
    GET_ORDER_STATUS_TOOL: run_get_order_status,
    LIST_ACTIVE_PROMOTIONS_TOOL: run_list_active_promotions,
    GET_STORE_INFO_TOOL: run_get_store_info,
    GET_POLICY_TOOL: run_get_policy,
}


def dispatch_tool(name: str, arguments: dict[str, object], today: date) -> ToolResult:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return ToolResult(content=f"Unknown tool: {name}", is_error=True)
    try:
        return ToolResult(content=handler(arguments, today), is_error=False)
    except Exception as handler_error:
        LOGGER.exception("Tool %s failed", name)
        return ToolResult(content=f"{type(handler_error).__name__}: {handler_error}", is_error=True)
