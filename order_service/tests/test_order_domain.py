
import pytest

from src.constants import OrderState, RejectionReason
from src.events import OrderCreatedEvent
from src.models import Order


def test_order_produce_created_event_on_create():
    order = Order.create(customer_id=1, order_total=100)

    for event in order.events:
        if isinstance(event, OrderCreatedEvent):
            event_data = event.data
            assert event_data["customer_id"] == 1
            assert event_data["order_total"] == 100
            break
    else:
        assert False, "order has not produced order_created event"


def test_order_customer_not_found():
    order = Order.create(customer_id=1, order_total=100)

    order.customer_not_found()

    assert order.state == OrderState.REJECTED
    assert order.rejection_reason == RejectionReason.UNKNOWN_CUSTOMER

def test_order_limit_exceeded():
    order = Order.create(customer_id=1, order_total=100)


    order.credit_limit_exceeded()

    assert order.state == OrderState.REJECTED
    assert order.rejection_reason == RejectionReason.INSUFFICIENT_CREDIT


def test_order_credit_reservation():
    order = Order.create(customer_id=1, order_total=100)

    order.credit_reservation()

    assert order.state == OrderState.APPROVED

def test_order_credit_cancel():
    order = Order.create(customer_id=1, order_total=100)
    order.credit_reservation()

    order.cancel()

    assert order.state == OrderState.CANCELLED
