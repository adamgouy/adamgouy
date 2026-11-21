# 03 - OOP: operator overloading and inheritance

Exercise: https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc (slide 67)

```bash
python operator_overloading.py
python inheritance.py
python -m pytest        # from the repository root
```

## Operator overloading - [`operator_overloading.py`](operator_overloading.py)

Python turns each operator into a method call: `a + b` → `a.__add__(b)`, `a > b` → `a.__gt__(b)`.

| Class | Operators | Meaning |
|---|---|---|
| `Complex` | `+`, `-`, `==` | add / subtract real and imaginary parts |
| `Person` | `>` | compares the ages |
| `Vector` | `*` | dot product: `x1*x2 + y1*y2 + z1*z2` |
| `Circle` | `==`, `!=`, `<`, `<=`, `>`, `>=` | compares the radius (the 6 methods written by hand) |
| `Point` | all comparisons | distance to the origin, with `@total_ordering` |
| `Matrix` | `*`, `==` | matrix product, with a dimension check |

What I learned:

- `__eq__` should return `NotImplemented` (not `False`) when the other object has another type:
  Python then tries the other object's `__eq__` before deciding.
- `Circle` and `Point` do the same job in two ways. In `Circle` the 6 comparison methods are written
  one by one. In `Point`, `@functools.total_ordering` generates `<=`, `>` and `>=` from `__eq__` and
  `__lt__`, which is shorter and avoids inconsistencies.
- `Point.__eq__` uses `math.isclose` because distances are floats (`0.1 + 0.2 != 0.3` in Python).

## Inheritance - [`inheritance.py`](inheritance.py)

| Parent | Children | What is inherited / overridden |
|---|---|---|
| `Vehicle` | `Car`, `Bicycle` | each child overrides `drive()` (polymorphism) |
| `Person` | `Student`, `Employee` | `super().__init__()` sets the common attributes, `introduce()` extends the parent's sentence |
| `BankAccount` | `SavingsAccount` | the savings account reuses deposit / withdraw / transfer and adds `add_interest()` |

Design choices for the bank accounts:

- The balance is stored in `_balance` and exposed with a read-only `@property`: it can only change
  through `deposit`, `withdraw` and `transfer`, which check the amounts (encapsulation).
- Errors raise exceptions (`ValueError`, `InsufficientFundsError`) instead of printing a message, so
  the calling code knows that the operation failed.
- `transfer` withdraws **before** depositing: if the withdrawal fails, the other account is not credited.
