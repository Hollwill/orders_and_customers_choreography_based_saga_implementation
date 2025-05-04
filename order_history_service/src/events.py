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


class OrderCreatedEvent(Event):
    def __init__(self, customer_id: int, order_total: int):
        self.customer_id = customer_id
        self.order_total = order_total

    exchange = "order.order"

    key = "order.created"

    @property
    def data(self) -> dict:
        return {"customer_id": self.customer_id, "order_total": self.order_total}

class OrderCanceledEvent(Event):
    def __init__(self, customer_id: int):
        self.customer_id = customer_id

    exchange = "order.order"

    key = "order.canceled"

    @property
    def data(self) -> dict:
        return {"customer_id": self.customer_id}