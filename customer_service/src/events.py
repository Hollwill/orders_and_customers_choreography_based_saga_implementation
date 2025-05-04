from abc import ABC, abstractmethod, abstractproperty



class Event(ABC):

    @property
    @abstractmethod
    def exchange(self):
        pass

    @property
    @abstractmethod
    def key(self):
        pass

    @property
    @abstractmethod
    def data(self) -> dict:
        pass

class CustomerNotFoundEvent(Event):
    def __init__(self, order_id):
        self.order_id = order_id

    exchange = "customer.customer"

    key = "customer.customer_not_found"

    @property
    def data(self) -> dict:
        return {"order_id": self.order_id}

class CustomerCreditReservationEvent(Event):
    def __init__(self, order_id):
        self.order_id = order_id


    exchange = "customer.customer"

    key = "customer.customer_credit_reservation"

    @property
    def data(self) -> dict:
        return {"order_id": self.order_id}

class CustomerCreditLimitExceededEvent(Event):
    def __init__(self, order_id):
        self.order_id = order_id


    exchange = "customer.customer"

    key = "customer.customer_credit_limit_exceeded"

    @property
    def data(self) -> dict:
        return {"order_id": self.order_id}

class CustomerCreatedEvent(Event):
    def __init__(self, money_limit: int, name: str):
        self.money_limit = money_limit
        self.name = name

    exchange = "customer.customer"

    key = "customer.customer_created"

    @property
    def data(self) -> dict:
        return {"money_limit": self.money_limit, "name": self.name}


# class OrderCreatedEvent(Event):
#     def __init__(self, customer_id: int, order_total: int):
#         self.customer_id = customer_id
#         self.order_total = order_total
#
#     exchange = "order.order"
#
#     key = "order.created"
#
#     @property
#     def data(self) -> dict:
#         return {"customer_id": self.customer_id, "order_total": self.order_total}
