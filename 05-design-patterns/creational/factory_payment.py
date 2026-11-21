"""Factory pattern - payment processing system.

Problems of the original code:
- `process_payment()` has one if/elif branch per payment method. Adding Apple Pay means editing a
  function that already works: it breaks the Open/Closed principle.
- Validation, fee calculation and processing of every method are mixed in one function: it breaks
  the Single Responsibility principle, and one method cannot be tested alone.
- The client code repeats the method names as strings and depends on all the details.

Solution: one class per payment method, all following the same `PaymentProcessor` interface, and a
`PaymentFactory` that turns a name ("paypal") into the right object. The client only talks to the
interface. New methods register themselves in the factory, which is never modified.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable


class PaymentProcessor(ABC):
    """Common interface. `process` is the same for every method, only the details change."""

    method = "generic"

    def process(self, amount: float, details: dict) -> dict:
        if amount <= 0:
            return {"success": False, "method": self.method, "error": "Amount must be positive"}
        error = self.validate(details)
        if error:
            return {"success": False, "method": self.method, "error": error}
        fee = round(self.compute_fee(amount), 2)
        return {"success": True, "method": self.method, "amount": round(amount + fee, 2), "fee": fee}

    @abstractmethod
    def validate(self, details: dict) -> str | None:
        """Return an error message, or None when the details are valid."""

    @abstractmethod
    def compute_fee(self, amount: float) -> float: ...


class PaymentFactory:
    """Creates processors from their name. The registry replaces the if/elif chain."""

    _registry: dict[str, type[PaymentProcessor]] = {}

    @classmethod
    def register(cls, name: str, processor: type[PaymentProcessor] | None = None):
        """Register a processor class. Works as a call or as a class decorator:

            PaymentFactory.register("cash", CashProcessor)
            @PaymentFactory.register("cash")
            class CashProcessor(PaymentProcessor): ...
        """
        def add(processor_cls: type[PaymentProcessor]) -> type[PaymentProcessor]:
            processor_cls.method = name
            cls._registry[name] = processor_cls
            return processor_cls

        return add(processor) if processor is not None else add

    @classmethod
    def available_methods(cls) -> list[str]:
        return sorted(cls._registry)

    def get_processor(self, payment_type: str) -> PaymentProcessor:
        processor_cls = self._registry.get(payment_type)
        if processor_cls is None:
            raise ValueError(
                f"Unknown payment type '{payment_type}'. "
                f"Available: {', '.join(self.available_methods())}"
            )
        return processor_cls()


# ---------------------------------------------------------------------------
# Concrete processors: each one only knows its own rules
# ---------------------------------------------------------------------------

def _digits(value) -> str:
    return str(value or "").replace(" ", "")


@PaymentFactory.register("credit_card")
class CreditCardProcessor(PaymentProcessor):
    def validate(self, details: dict) -> str | None:
        card, cvv = _digits(details.get("card_number")), _digits(details.get("cvv"))
        if len(card) != 16 or not card.isdigit():
            return "Invalid card number"
        if len(cvv) != 3 or not cvv.isdigit():
            return "Invalid CVV"
        return None

    def compute_fee(self, amount: float) -> float:
        return amount * 0.029                 # 2.9 %


@PaymentFactory.register("bank_transfer")
class BankTransferProcessor(PaymentProcessor):
    def validate(self, details: dict) -> str | None:
        iban = _digits(details.get("iban"))
        if len(iban) < 15 or not iban[:2].isalpha():
            return "Invalid IBAN"
        return None

    def compute_fee(self, amount: float) -> float:
        return 1.50                           # flat fee


@PaymentFactory.register("paypal")
class PayPalProcessor(PaymentProcessor):
    def validate(self, details: dict) -> str | None:
        email = str(details.get("email") or "")
        user, _, domain = email.partition("@")
        if not user or "." not in domain:
            return "Invalid PayPal email"
        return None

    def compute_fee(self, amount: float) -> float:
        return amount * 0.034 + 0.30          # 3.4 % + 0.30


# ---------------------------------------------------------------------------
# Extension test: Apple Pay is added WITHOUT touching the factory or the other classes
# ---------------------------------------------------------------------------

@PaymentFactory.register("apple_pay")
class ApplePayProcessor(PaymentProcessor):
    def validate(self, details: dict) -> str | None:
        return None if details.get("device_token") else "Missing Apple Pay device token"

    def compute_fee(self, amount: float) -> float:
        return amount * 0.02                  # 2 %


if __name__ == "__main__":
    factory = PaymentFactory()
    print("Available methods:", factory.available_methods())

    payments: list[tuple[str, float, dict]] = [
        ("credit_card", 100.0, {"card_number": "4970 1234 5678 9012", "cvv": "123"}),
        ("bank_transfer", 100.0, {"iban": "FR76 3000 6000 0112 3456 7890 189"}),
        ("paypal", 100.0, {"email": "not-an-email"}),
        ("apple_pay", 100.0, {"device_token": "tok_7f3a"}),
    ]
    for method, amount, details in payments:
        print(f"{method:>13}:", factory.get_processor(method).process(amount, details))

    try:
        factory.get_processor("bitcoin")
    except ValueError as error:
        print("Error:", error)
