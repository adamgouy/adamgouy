"""ABCD Records - implementation of the class diagram in abcd_records.md.

Run: python abcd_records.py
"""
from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from datetime import date
from enum import Enum


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

class Customer:
    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r})"


class Member(Customer):
    def __init__(self, member_id: str, name: str, address: str):
        super().__init__(name, address)
        self.member_id = member_id

    def discount_rate(self) -> float:
        return 0.0

    def can_backorder(self) -> bool:
        return False


class RoyalMember(Member):
    def discount_rate(self) -> float:
        return 0.10

    def can_backorder(self) -> bool:
        return True


class MembershipApplication:
    def __init__(self, customer: Customer):
        self.customer = customer
        self.sent_on = date.today()


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

class Item(ABC):
    def __init__(self, reference: str, title: str, price: float, stock: int):
        self.reference = reference
        self.title = title
        self.price = price
        self.stock = stock

    def is_available(self, quantity: int) -> bool:
        return self.stock >= quantity

    def remove_from_stock(self, quantity: int) -> None:
        if not self.is_available(quantity):
            raise ValueError(f"Not enough stock for {self.title}")
        self.stock -= quantity

    def restock(self, quantity: int) -> None:
        self.stock += quantity

    @abstractmethod
    def media(self) -> str: ...


class CD(Item):
    def __init__(self, reference: str, title: str, price: float, stock: int, artist: str, tracks: int):
        super().__init__(reference, title, price, stock)
        self.artist = artist
        self.tracks = tracks

    def media(self) -> str:
        return "CD"


class Tape(Item):
    def __init__(self, reference: str, title: str, price: float, stock: int, artist: str, length_min: int):
        super().__init__(reference, title, price, stock)
        self.artist = artist
        self.length_min = length_min

    def media(self) -> str:
        return "Tape"


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class OrderStatus(Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    PAID = "paid"


class OrderLine:
    def __init__(self, item: Item, quantity: int, backordered: bool = False):
        if quantity <= 0:
            raise ValueError("The quantity must be positive")
        self.item = item
        self.quantity = quantity
        self.backordered = backordered

    def amount(self) -> float:
        return self.item.price * self.quantity


class Order:
    _ids = itertools.count(1)

    def __init__(self, member: Member):
        self.order_id = next(self._ids)
        self.member = member
        self.order_date = date.today()
        self.status = OrderStatus.RECEIVED
        self.lines: list[OrderLine] = []

    def add_line(self, item: Item, quantity: int, backordered: bool = False) -> OrderLine:
        line = OrderLine(item, quantity, backordered)
        self.lines.append(line)
        return line

    def subtotal(self) -> float:
        return sum(line.amount() for line in self.lines)

    def discount(self) -> float:
        return round(self.subtotal() * self.member.discount_rate(), 2)

    def total(self) -> float:
        return round(self.subtotal() - self.discount(), 2)


class Invoice:
    def __init__(self, order: Order):
        self.order = order
        self.amount = order.total()
        self.paid = False

    def print(self) -> str:
        rows = [f"INVOICE - order #{self.order.order_id} - {self.order.member.name}"]
        for line in self.order.lines:
            note = " (backordered)" if line.backordered else ""
            rows.append(f"  {line.quantity} x {line.item.title:<28} {line.amount():>7.2f}{note}")
        if self.order.discount():
            rows.append(f"  {'Royal discount':<32} {-self.order.discount():>7.2f}")
        rows.append(f"  {'TOTAL':<32} {self.amount:>7.2f}")
        return "\n".join(rows)


class ShippingList:
    def __init__(self, order: Order):
        self.order = order
        self.lines = [line for line in order.lines if not line.backordered]

    def print(self) -> str:
        rows = [f"SHIPPING LIST - order #{self.order.order_id} - to {self.order.member.address}"]
        rows += [f"  {line.quantity} x {line.item.media()} {line.item.title}" for line in self.lines]
        return "\n".join(rows)


class DailyRecordFile:
    def __init__(self, day: date | None = None):
        self.day = day or date.today()
        self.orders: list[Order] = []

    def record(self, order: Order) -> None:
        self.orders.append(order)


class Supplier:
    def __init__(self):
        self.pending: list[tuple[Item, int]] = []

    def reorder(self, item: Item, quantity: int) -> None:
        self.pending.append((item, quantity))

    def deliver_all(self) -> None:
        for item, quantity in self.pending:
            item.restock(quantity)
        self.pending.clear()


# ---------------------------------------------------------------------------
# Payments (Strategy pattern)
# ---------------------------------------------------------------------------

class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount: float) -> str: ...


class Cash(PaymentMethod):
    def pay(self, amount: float) -> str:
        return f"{amount:.2f} EUR paid in cash"


class Check(PaymentMethod):
    def __init__(self, number: str, bank: str):
        self.number, self.bank = number, bank

    def pay(self, amount: float) -> str:
        return f"{amount:.2f} EUR paid by check n°{self.number} ({self.bank})"


class BankDraft(PaymentMethod):
    def __init__(self, number: str):
        self.number = number

    def pay(self, amount: float) -> str:
        return f"{amount:.2f} EUR paid by bank draft n°{self.number}"


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

class NotAMemberError(Exception):
    def __init__(self, application: MembershipApplication):
        super().__init__(f"{application.customer.name} is not a member: application form sent")
        self.application = application


class OrderProcessingClerk:
    def __init__(self, members: dict[str, Member], supplier: Supplier, records: DailyRecordFile):
        self.members = members
        self.supplier = supplier
        self.records = records

    def verify_membership(self, customer: Customer) -> bool:
        return isinstance(customer, Member) and customer.member_id in self.members

    def place_order(self, customer: Customer, items: list[tuple[Item, int]]) -> Order:
        if not self.verify_membership(customer):
            raise NotAMemberError(MembershipApplication(customer))
        order = Order(customer)
        for item, quantity in items:
            if item.is_available(quantity):
                item.remove_from_stock(quantity)
                order.add_line(item, quantity)
            elif customer.can_backorder():
                self.supplier.reorder(item, quantity)
                order.add_line(item, quantity, backordered=True)
            # a regular member's unavailable item is simply not ordered
        return order

    def process(self, order: Order) -> tuple[Invoice, ShippingList]:
        invoice, shipping = Invoice(order), ShippingList(order)
        order.status = OrderStatus.PROCESSED
        self.records.record(order)
        return invoice, shipping


class CollectionClerk:
    def collect(self, invoice: Invoice, method: PaymentMethod) -> str:
        if invoice.paid:
            raise ValueError("This invoice is already paid")
        receipt = method.pay(invoice.amount)
        invoice.paid = True
        invoice.order.status = OrderStatus.PAID
        return receipt


if __name__ == "__main__":
    royal = RoyalMember("M-007", "Ines Laurent", "12 rue des Lilas, 69003 Lyon")
    supplier, records = Supplier(), DailyRecordFile()
    clerk = OrderProcessingClerk({royal.member_id: royal}, supplier, records)

    cd = CD("CD-101", "Random Access Memories", 15.90, stock=4, artist="Daft Punk", tracks=13)
    tape = Tape("TP-202", "Rumours", 9.50, stock=0, artist="Fleetwood Mac", length_min=39)

    order = clerk.place_order(royal, [(cd, 2), (tape, 1)])
    invoice, shipping = clerk.process(order)
    print(invoice.print(), "\n")
    print(shipping.print(), "\n")
    print("Receipt:", CollectionClerk().collect(invoice, Check("0042117", "La Banque Postale")))
    print("Reordered from supplier:", [(item.title, qty) for item, qty in supplier.pending])

    try:
        clerk.place_order(Customer("Paul Moreau", "3 avenue Foch, Paris"), [(cd, 1)])
    except NotAMemberError as error:
        print("\nRefused:", error)
