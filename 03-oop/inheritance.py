"""Inheritance exercises.

Statement: https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc (slide 67)

A child class gets every attribute and method of its parent, and can override
(redefine) some of them. `super()` calls the parent's version, which avoids
copy-pasting the parent's code.
"""
from __future__ import annotations


# --- Vehicle / Car / Bicycle --------------------------------------------------

class Vehicle:
    def __init__(self, brand: str = "unknown"):
        self.brand = brand

    def drive(self) -> str:
        return f"The {self.brand} vehicle is moving"


class Car(Vehicle):
    def drive(self) -> str:   # override
        return f"The {self.brand} car is driving on the road"


class Bicycle(Vehicle):
    def drive(self) -> str:   # override
        return f"The {self.brand} bicycle is being pedaled"


# --- Person / Student / Employee ----------------------------------------------

class Person:
    def __init__(self, name: str, age: int, address: str):
        self.name = name
        self.age = age
        self.address = address

    def introduce(self) -> str:
        return f"My name is {self.name}, I am {self.age} and I live in {self.address}."


class Student(Person):
    def __init__(self, name: str, age: int, address: str, school: str, program: str):
        super().__init__(name, age, address)   # the parent sets name, age and address
        self.school = school
        self.program = program

    def introduce(self) -> str:
        return f"{super().introduce()} I study {self.program} at {self.school}."


class Employee(Person):
    def __init__(self, name: str, age: int, address: str, company: str, job_title: str):
        super().__init__(name, age, address)
        self.company = company
        self.job_title = job_title

    def introduce(self) -> str:
        return f"{super().introduce()} I work as a {self.job_title} at {self.company}."


# --- BankAccount / SavingsAccount ---------------------------------------------

class InsufficientFundsError(Exception):
    """Raised when an account does not have enough money for an operation."""


class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        if balance < 0:
            raise ValueError("The initial balance cannot be negative")
        self.owner = owner
        self._balance = balance   # "_" = internal: change it only through the methods

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        self._check_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        self._check_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError(
                f"{self.owner} cannot withdraw {amount:.2f}: balance is {self._balance:.2f}"
            )
        self._balance -= amount

    def transfer(self, amount: float, target: BankAccount) -> None:
        # withdraw first: if it fails, the target account is never credited
        self.withdraw(amount)
        target.deposit(amount)

    def check_balance(self) -> float:
        return self._balance

    @staticmethod
    def _check_amount(amount: float) -> None:
        if amount <= 0:
            raise ValueError("The amount must be positive")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.owner!r}, balance={self._balance:.2f})"


class SavingsAccount(BankAccount):
    def __init__(self, owner: str, balance: float = 0.0, interest_rate: float = 0.03):
        super().__init__(owner, balance)
        if not 0 <= interest_rate < 1:
            raise ValueError("The interest rate must be between 0 and 1 (e.g. 0.03 for 3%)")
        self.interest_rate = interest_rate

    def add_interest(self) -> float:
        """Credit one period of interest and return the amount added."""
        interest = round(self._balance * self.interest_rate, 2)
        self._balance += interest
        return interest


if __name__ == "__main__":
    # Polymorphism: the same call, a different behavior for each class
    for vehicle in [Vehicle(), Car("Peugeot"), Bicycle("Decathlon")]:
        print(vehicle.drive())

    print()
    for person in [
        Person("Lina", 45, "Lyon"),
        Student("Yanis", 19, "Paris", "Sorbonne University", "mathematics"),
        Employee("Claire", 31, "Bordeaux", "Airbus", "data analyst"),
    ]:
        print(person.introduce())

    print()
    current = BankAccount("Yanis", 500)
    savings = SavingsAccount("Yanis", 2000, interest_rate=0.03)
    current.transfer(200, savings)
    print("After transfer:", current, savings)
    print("Interest added:", savings.add_interest(), "-> new balance:", savings.check_balance())
    try:
        current.withdraw(1000)
    except InsufficientFundsError as error:
        print("Refused:", error)
