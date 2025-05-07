

from src.events import CustomerCreatedEvent, CustomerCreditReservationEvent, CustomerCreditLimitExceededEvent
from src.models import Customer
from src.schemas import OrderCreatedSchema


def test_customer_create():
    customer = Customer.create(name="test", money_limit=100)

    for event in customer.events:
        if isinstance(event, CustomerCreatedEvent):
            event_data = event.data
            assert event_data["money_limit"] == 100
            assert event_data["name"] == "test"
            break
    else:
        assert False, "customer has not produced customer_created event"


def test_customer_reserve_credit_success():
    customer = Customer.create(name="test", money_limit=100)

    customer.reserve_credit(OrderCreatedSchema(aggregate_id=1, customer_id=2, order_total=100))


    assert customer.money_limit == 0

    assert customer.credit_reservations

    assert customer.credit_reservations[0].order_id == 1
    assert customer.credit_reservations[0].amount == 100

    for event in customer.events:
        if isinstance(event, CustomerCreditReservationEvent):
            assert event.data["order_id"] == 1
            break
    else:
        assert False, "customer has not produced customer_created event"

def test_customer_reserve_credit_failed():
    customer = Customer.create(name="test", money_limit=100)

    customer.reserve_credit(OrderCreatedSchema(aggregate_id=1, customer_id=2, order_total=101))


    assert customer.money_limit == 100

    assert not customer.credit_reservations

    for event in customer.events:
        if isinstance(event, CustomerCreditLimitExceededEvent):
            assert event.data["order_id"] == 1
            break
    else:
        assert False, "customer has not produced customer_created event"

def test_customer_unreserve_credit():
    customer = Customer.create(name="test", money_limit=100)
    customer.reserve_credit(OrderCreatedSchema(aggregate_id=1, customer_id=2, order_total=100))

    customer.unreserve_credit(1)

    assert  customer.credit_reservations

    assert customer.credit_reservations[0].deleted_at is not None
