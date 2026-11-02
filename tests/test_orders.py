from dataclasses import asdict
from datetime import date
from decimal import Decimal

import pytest

from emporio_agent.catalog import (
    AMBIGUOUS_CONTACT,
    ORDER_NOT_FOUND,
    OrderDetail,
    get_order_status,
)

TODAY = date(2026, 11, 1)
LUCAS_EMAIL = "lucas.mendes@jmail.com"
SHARED_EMAIL = "bruno.martins@jmail.com"
BRUNO_CARVALHO_MARTINS_PHONE = "(67) 98543-2109"
BRUNO_MARTINS_PHONE = "(67) 99456-3456"


def found_order(
    order_id: int, customer_email: str | None, customer_phone: str | None
) -> OrderDetail:
    order_status = get_order_status(order_id, customer_email, customer_phone, TODAY)
    assert isinstance(order_status, OrderDetail)
    return order_status


def test_unknown_order_returns_generic_not_found() -> None:
    assert get_order_status(999, LUCAS_EMAIL, None, TODAY) == ORDER_NOT_FOUND


def test_order_of_another_customer_returns_the_same_generic_object() -> None:
    assert get_order_status(10, LUCAS_EMAIL, None, TODAY) is get_order_status(
        999, LUCAS_EMAIL, None, TODAY
    )
    assert ORDER_NOT_FOUND.message.startswith("Não localizei um pedido com esses dados.")


def test_missing_contact_raises_validation_error() -> None:
    with pytest.raises(ValueError, match="customer_email or customer_phone"):
        get_order_status(10, None, None, TODAY)


def test_shared_email_requires_phone() -> None:
    assert get_order_status(10, SHARED_EMAIL, None, TODAY) == AMBIGUOUS_CONTACT
    assert get_order_status(10, SHARED_EMAIL, None, TODAY).found is False
    assert "telefone" in AMBIGUOUS_CONTACT.message


@pytest.mark.parametrize("blank_phone", ["", "   ", "sem telefone"])
def test_shared_email_with_blank_phone_requires_phone(blank_phone: str) -> None:
    assert get_order_status(10, SHARED_EMAIL, blank_phone, TODAY) == AMBIGUOUS_CONTACT


def test_shared_email_with_wrong_phone_is_not_found() -> None:
    assert get_order_status(10, SHARED_EMAIL, BRUNO_MARTINS_PHONE, TODAY) == ORDER_NOT_FOUND


def test_phone_of_the_other_customer_with_shared_email_is_not_found() -> None:
    assert get_order_status(10, None, BRUNO_MARTINS_PHONE, TODAY) == ORDER_NOT_FOUND


def test_owner_phone_unlocks_order_with_or_without_mask() -> None:
    order = found_order(10, None, BRUNO_CARVALHO_MARTINS_PHONE)
    assert order.customer_first_name == "Bruno"
    assert order.total_brl == Decimal("8732.00")
    assert found_order(10, SHARED_EMAIL, "67985432109").order_id == 10
    assert found_order(10, None, "67 98543 2109").order_id == 10


def test_email_comparison_ignores_case_and_spaces() -> None:
    order = found_order(4, "  LUCAS.MENDES@JMAIL.COM ", None)
    assert order.order_id == 4
    assert order.customer_first_name == "Lucas"


def test_order_payload_never_contains_contact_data() -> None:
    payload = asdict(found_order(10, None, BRUNO_CARVALHO_MARTINS_PHONE))
    assert not {"phone", "email", "city", "customer_id", "customer_name"} & set(payload)
    assert "Carvalho" not in str(payload)
    assert payload["delivery_city"] == "Três Lagoas"


def test_order_total_is_the_amount_paid_not_the_sum_of_items() -> None:
    order_3 = found_order(3, "isabela.moreira@jmail.com", None)
    assert order_3.total_brl == Decimal("3450.00")
    assert len(order_3.items) == 1
    assert order_3.items[0].product_name == "Kala KA-ABP-CTG Barítono Cedar"
    assert order_3.items[0].quantity == 2
    order_20 = found_order(20, "thiago.barbosa@jmail.com", None)
    assert order_20.total_brl == Decimal("1400.00")
    assert {order_item.product_name for order_item in order_20.items} == {
        "Giannini GN-15 Nylon Cedr Natural",
        "Shelby SGD-195E Elétrico Aço Sunburst",
    }


def test_cancelled_order_exposes_reason_and_no_tracking() -> None:
    order = found_order(17, "matheus.correia@hayoo.com.br", None)
    assert order.status == "cancelled"
    assert order.status_label == "cancelado"
    assert order.cancellation_reason == "Pedido cancelado pelo cliente antes do processamento"
    assert order.tracking_code is None
    assert order.estimated_delivery is None
    assert order.total_brl == Decimal("689.00")
    assert order.payment_method_label == "PIX"


def test_shipped_order_exposes_tracking_and_overdue_estimate() -> None:
    order = found_order(8, "anacarol.ferreira@coldmail.com", None)
    assert order.status == "shipped"
    assert order.status_label == "enviado"
    assert order.tracking_code == "BRJL5544332BR"
    assert order.estimated_delivery == date(2026, 2, 28)
    assert order.estimated_delivery_has_passed is True
    assert order.payment_method_label == "cartão de débito"
    assert order.cancellation_reason is None
    assert order.received_on is None
    assert order.withdrawal_window_open is None


def test_pending_order_has_no_tracking_or_windows() -> None:
    order = found_order(13, "fernanda.ribeiro@coldmail.com", None)
    assert order.status == "pending"
    assert order.status_label == "pendente"
    assert order.tracking_code is None
    assert order.estimated_delivery is None
    assert order.estimated_delivery_has_passed is None
    assert order.withdrawal_deadline is None
    assert order.defect_exchange_window_open is None


def test_delivered_order_windows_closed_today() -> None:
    order = found_order(4, LUCAS_EMAIL, None)
    assert order.status_label == "entregue"
    assert order.received_on == date(2025, 12, 22)
    assert order.estimated_delivery == date(2025, 12, 22)
    assert order.estimated_delivery_has_passed is None
    assert order.withdrawal_deadline == date(2025, 12, 29)
    assert order.withdrawal_window_open is False
    assert order.defect_exchange_deadline == date(2026, 1, 9)
    assert order.defect_exchange_window_open is False


@pytest.mark.parametrize(
    ("today", "expected_open"),
    [
        (date(2025, 12, 24), True),
        (date(2025, 12, 29), True),
        (date(2025, 12, 30), False),
    ],
)
def test_withdrawal_window_is_inclusive_of_the_deadline(today: date, expected_open: bool) -> None:
    order_status = get_order_status(4, LUCAS_EMAIL, None, today)
    assert isinstance(order_status, OrderDetail)
    assert order_status.withdrawal_window_open is expected_open


@pytest.mark.parametrize(
    ("today", "expected_open"),
    [
        (date(2026, 1, 9), True),
        (date(2026, 1, 10), False),
    ],
)
def test_defect_exchange_window_counts_30_days_from_purchase(
    today: date, expected_open: bool
) -> None:
    order_status = get_order_status(4, LUCAS_EMAIL, None, today)
    assert isinstance(order_status, OrderDetail)
    assert order_status.defect_exchange_window_open is expected_open


def test_payment_method_labels_in_portuguese() -> None:
    assert found_order(2, "thiago.barbosa@jmail.com", None).payment_method_label == (
        "cartão de crédito em 6x"
    )
    assert found_order(4, LUCAS_EMAIL, None).payment_method_label == "boleto bancário"
    assert found_order(15, "aline.monteiro@jmail.com", None).payment_method_label == (
        "cartão de crédito em 12x"
    )
