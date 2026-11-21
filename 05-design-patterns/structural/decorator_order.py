"""Decorator pattern - order pricing.

Problems of the original code:
- `calculate_total()` has one boolean flag per option (express, insurance, gift wrap, discount,
  premium): every new option adds a parameter and an `if` (flag explosion);
- one method does all the calculations: it breaks the Single Responsibility principle;
- adding an option means editing that method: it breaks the Open/Closed principle;
- the order of the operations is hidden in the code (is the discount applied before or after
  the shipping?) and the options cannot be reused elsewhere.

Solution: every option is a small class that WRAPS an order and adds its own effect. Decorators
have the same interface as the order they wrap, so they can be stacked in any number and any
order, and the stacking order is exactly the order of the calculation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class OrderComponent(ABC):
    @abstractmethod
    def get_cost(self) -> float: ...

    @abstractmethod
    def get_description(self) -> str: ...


class BaseOrder(OrderComponent):
    def __init__(self, base_price: float):
        if base_price < 0:
            raise ValueError("The price cannot be negative")
        self.base_price = base_price

    def get_cost(self) -> float:
        return self.base_price

    def get_description(self) -> str:
        return f"Base price{'':>17}{self.base_price:>8.2f}"


class OrderDecorator(OrderComponent):
    """Parent of every option: wraps an order and adds one line + one amount to it."""

    label = "option"

    def __init__(self, order: OrderComponent):
        self._wrapped = order

    @abstractmethod
    def extra(self) -> float:
        """Amount added (negative for a reduction), computed from the wrapped order."""

    def get_cost(self) -> float:
        return round(self._wrapped.get_cost() + self.extra(), 2)

    def get_description(self) -> str:
        return f"{self._wrapped.get_description()}\n{self.label:<27}{self.extra():>+8.2f}"


class ExpressShippingDecorator(OrderDecorator):
    label = "Express shipping"

    def extra(self) -> float:
        return 15.00


class InsuranceDecorator(OrderDecorator):
    label = "Insurance (5%)"

    def extra(self) -> float:
        return round(self._wrapped.get_cost() * 0.05, 2)


class GiftWrapDecorator(OrderDecorator):
    label = "Gift wrap"

    def extra(self) -> float:
        return 5.00


class DiscountDecorator(OrderDecorator):
    def __init__(self, order: OrderComponent, percent: float):
        super().__init__(order)
        if not 0 < percent <= 100:
            raise ValueError("The discount must be between 0 and 100 %")
        self.percent = percent
        self.label = f"Discount ({percent:g}%)"

    def extra(self) -> float:
        return -round(self._wrapped.get_cost() * self.percent / 100, 2)


class PremiumMemberDecorator(DiscountDecorator):
    """A premium member always gets 10 %: it is a discount with a fixed rate."""

    def __init__(self, order: OrderComponent):
        super().__init__(order, percent=10)
        self.label = "Premium member (10%)"


def receipt(order: OrderComponent) -> str:
    return f"{order.get_description()}\n{'-' * 35}\n{'TOTAL':<27}{order.get_cost():>8.2f}"


if __name__ == "__main__":
    print(receipt(BaseOrder(100.00)), "\n")

    # Read from the inside out: insurance on the base price, then shipping and gift wrap,
    # then the 15 % discount, then the premium discount on what is left.
    order = PremiumMemberDecorator(
        DiscountDecorator(
            GiftWrapDecorator(
                ExpressShippingDecorator(
                    InsuranceDecorator(BaseOrder(100.00)))),
            percent=15))
    print(receipt(order), "\n")

    # Same options, other order: the discount no longer applies to the shipping.
    other = ExpressShippingDecorator(DiscountDecorator(BaseOrder(100.00), percent=15))
    print(receipt(other))
