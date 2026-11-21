"""Online hospital management system - implementation of the class diagram in hospital.md.

Run: python hospital.py
"""
from __future__ import annotations

import hashlib
import itertools
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class ProblemStatus(Enum):
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    PRESCRIBED = "prescribed"
    CLOSED = "closed"


class PaymentStatus(Enum):
    RECEIVED = "received"
    FORWARDED = "forwarded"


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------

class Member(ABC):
    def __init__(self, name: str, password: str):
        self.member_id: str | None = None   # given by the system at registration
        self.name = name
        self._password_hash = self._hash(password)

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self._hash(password) == self._password_hash

    @abstractmethod
    def role(self) -> str: ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.member_id}, {self.name!r})"


class Patient(Member):
    def __init__(self, name: str, password: str):
        super().__init__(name, password)
        self.problems: list[HealthProblem] = []

    def role(self) -> str:
        return "patient"

    def post_problem(self, description: str) -> HealthProblem:
        problem = HealthProblem(self, description)
        self.problems.append(problem)
        return problem

    def prescriptions(self) -> list[Prescription]:
        return [p.prescription for p in self.problems if p.prescription is not None]

    def pay(self, prescription: Prescription, method: PaymentMethod) -> Payment:
        if prescription.problem.patient is not self:
            raise PermissionError("A patient can only pay his own prescriptions")
        if prescription.payment is not None:
            raise ValueError("This prescription is already paid")
        receipt = method.pay(prescription.fee)
        payment = Payment(prescription, method, receipt)
        prescription.payment = payment
        prescription.problem.status = ProblemStatus.CLOSED
        return payment


class Doctor(Member):
    def __init__(self, name: str, password: str, speciality: str):
        super().__init__(name, password)
        self.speciality = speciality
        self.earnings = 0.0

    def role(self) -> str:
        return "doctor"

    def prescribe(self, problem: HealthProblem, treatment: str, fee: float) -> Prescription:
        if problem.doctor is not self:
            raise PermissionError("Only the doctor in charge can write the prescription")
        if problem.status is not ProblemStatus.ASSIGNED:
            raise ValueError(f"Cannot prescribe for a problem in status {problem.status.value}")
        problem.prescription = Prescription(problem, treatment, fee)
        problem.status = ProblemStatus.PRESCRIBED
        return problem.prescription

    def receive(self, amount: float) -> None:
        self.earnings += amount


class Organizer(Member):
    def role(self) -> str:
        return "organizer"

    def assign(self, problem: HealthProblem, doctor: Doctor) -> None:
        if problem.status is not ProblemStatus.SUBMITTED:
            raise ValueError("This problem is already handled")
        problem.doctor = doctor
        problem.status = ProblemStatus.ASSIGNED

    def deliver_prescription(self, problem: HealthProblem) -> Prescription:
        if problem.prescription is None:
            raise ValueError("No prescription to deliver yet")
        return problem.prescription

    def forward_payment(self, payment: Payment) -> None:
        if payment.status is PaymentStatus.FORWARDED:   # integrity: never pay a doctor twice
            raise ValueError("This payment was already forwarded")
        payment.prescription.problem.doctor.receive(payment.amount)
        payment.status = PaymentStatus.FORWARDED


# ---------------------------------------------------------------------------
# Problems and prescriptions
# ---------------------------------------------------------------------------

class HealthProblem:
    _ids = itertools.count(1)

    def __init__(self, patient: Patient, description: str):
        if not description.strip():
            raise ValueError("The description cannot be empty")
        self.problem_id = next(self._ids)
        self.patient = patient
        self.description = description
        self.status = ProblemStatus.SUBMITTED
        self.created_at = datetime.now()
        self.doctor: Doctor | None = None
        self.prescription: Prescription | None = None   # composition: owned by the problem


class Prescription:
    def __init__(self, problem: HealthProblem, treatment: str, fee: float,
                 renewal_of: Prescription | None = None):
        if fee < 0:
            raise ValueError("The fee cannot be negative")
        self.problem = problem
        self.treatment = treatment
        self.fee = fee
        self.issued_at = datetime.now()
        self.renewal_of = renewal_of
        self.payment: Payment | None = None

    def renew(self) -> Prescription:
        """Reuse a treatment: a new prescription that keeps a link to this one."""
        return Prescription(self.problem, self.treatment, self.fee, renewal_of=self)


# ---------------------------------------------------------------------------
# Payments (Strategy pattern)
# ---------------------------------------------------------------------------

class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount: float) -> str:
        """Process the payment and return a receipt."""


class CashPayment(PaymentMethod):
    def pay(self, amount: float) -> str:
        return f"Cash payment of {amount:.2f} EUR received"


class CheckPayment(PaymentMethod):
    def __init__(self, check_number: str, bank: str):
        self.check_number = check_number
        self.bank = bank

    def pay(self, amount: float) -> str:
        return f"Check n°{self.check_number} ({self.bank}) of {amount:.2f} EUR received"


class CreditCardPayment(PaymentMethod):
    def __init__(self, card_number: str):
        digits = card_number.replace(" ", "")
        if len(digits) != 16 or not digits.isdigit():
            raise ValueError("A card number has 16 digits")
        self._last_digits = digits[-4:]   # never keep the full number

    def pay(self, amount: float) -> str:
        return f"Card ****{self._last_digits} charged {amount:.2f} EUR"


class Payment:
    def __init__(self, prescription: Prescription, method: PaymentMethod, receipt: str):
        self.prescription = prescription
        self.amount = prescription.fee
        self.method = method
        self.receipt = receipt
        self.status = PaymentStatus.RECEIVED
        self.paid_at = datetime.now()


# ---------------------------------------------------------------------------
# The system: registration and login
# ---------------------------------------------------------------------------

class HospitalSystem:
    PREFIXES = {"patient": "PAT", "doctor": "DOC", "organizer": "ORG"}

    def __init__(self):
        self.members: dict[str, Member] = {}
        self._counter = itertools.count(1)

    def register(self, member: Member) -> str:
        member.member_id = f"{self.PREFIXES[member.role()]}-{next(self._counter):04d}"
        self.members[member.member_id] = member
        return member.member_id

    def login(self, member_id: str, password: str) -> Member:
        member = self.members.get(member_id)
        if member is None or not member.check_password(password):
            raise PermissionError("Wrong id or password")   # same message: don't reveal which one
        return member


if __name__ == "__main__":
    system = HospitalSystem()
    organizer = Organizer("Nadia", "org-pass")
    doctor = Doctor("Dr Martin", "doc-pass", "neurology")
    patient = Patient("Hugo", "hugo-pass")
    for member in (organizer, doctor, patient):
        print("Registered:", system.register(member), member.name)

    me = system.login(patient.member_id, "hugo-pass")
    problem = me.post_problem("Strong headaches for a week")
    organizer.assign(problem, doctor)
    doctor.prescribe(problem, "Paracetamol 1g, 3 times a day for 5 days", fee=45.0)
    prescription = organizer.deliver_prescription(problem)
    print("Prescription:", prescription.treatment)

    payment = patient.pay(prescription, CreditCardPayment("4970 1234 5678 9012"))
    print("Receipt:", payment.receipt)
    organizer.forward_payment(payment)
    print(f"{doctor.name} earnings: {doctor.earnings:.2f} EUR | problem status: {problem.status.value}")
