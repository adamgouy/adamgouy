"""Builder pattern - HR employee onboarding.

Problems of the original code:
- `create_employee()` takes 17 positional parameters. Forgetting one `None` shifts all the next
  arguments, and Python does not notice when the types are the same.
- A call like `..., False, True, True, False, ...` is impossible to read: which boolean is the VPN?
- Validation is scattered, and the standard profiles (a developer always gets a laptop and VPN
  access, an intern never gets admin rights) are copied by hand at every call.

Solution:
- `EmployeeBuilder` builds the employee step by step with named methods that return `self`,
  so the calls can be chained and read like a sentence;
- all the validation happens in one place: `build()`;
- `OnboardingDirector` knows the standard recipes (developer, intern, manager): the "Director"
  of the Builder pattern. A preset can still be customised before calling `build()`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

CONTRACT_TYPES = {"permanent", "fixed-term", "internship", "freelance"}


@dataclass(frozen=True)
class Employee:
    """The product. frozen=True: once built, an employee record cannot be modified by mistake."""
    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    salary: float
    start_date: date
    manager_id: int | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    has_parking: bool = False
    has_laptop: bool = False
    has_vpn_access: bool = False
    has_admin_rights: bool = False
    office_location: str = "Remote"
    contract_type: str = "permanent"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class EmployeeBuilder:
    def __init__(self):
        self._fields: dict = {}

    # --- identity ----------------------------------------------------------
    def with_name(self, first_name: str, last_name: str) -> EmployeeBuilder:
        self._fields.update(first_name=first_name.strip(), last_name=last_name.strip())
        return self

    def with_email(self, email: str) -> EmployeeBuilder:
        self._fields["email"] = email.strip().lower()
        return self

    def with_contact(self, phone: str | None = None, address: str | None = None,
                     emergency_contact: str | None = None) -> EmployeeBuilder:
        self._fields.update(phone=phone, address=address, emergency_contact=emergency_contact)
        return self

    # --- job ---------------------------------------------------------------
    def with_job(self, department: str, position: str, salary: float) -> EmployeeBuilder:
        self._fields.update(department=department, position=position, salary=salary)
        return self

    def starting_on(self, start_date: str | date) -> EmployeeBuilder:
        self._fields["start_date"] = (
            date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
        )
        return self

    def with_manager(self, manager_id: int) -> EmployeeBuilder:
        self._fields["manager_id"] = manager_id
        return self

    def with_contract(self, contract_type: str) -> EmployeeBuilder:
        self._fields["contract_type"] = contract_type
        return self

    # --- equipment and access ---------------------------------------------
    def with_equipment(self, laptop: bool = False, parking: bool = False) -> EmployeeBuilder:
        self._fields.update(has_laptop=laptop, has_parking=parking)
        return self

    def with_access(self, vpn: bool = False, admin: bool = False) -> EmployeeBuilder:
        self._fields.update(has_vpn_access=vpn, has_admin_rights=admin)
        return self

    def at_office(self, location: str) -> EmployeeBuilder:
        self._fields["office_location"] = location
        return self

    # --- final step: every rule is checked here, once -----------------------
    def build(self) -> Employee:
        f = dict(self._fields)
        f.setdefault("start_date", date.today())

        missing = [k for k in ("first_name", "last_name", "email", "department", "position") if not f.get(k)]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")
        user, _, domain = f["email"].partition("@")
        if not user or "." not in domain:
            raise ValueError(f"Invalid email: {f['email']}")
        if f.get("salary", 0) < 0:
            raise ValueError("Salary cannot be negative")
        if f.get("contract_type", "permanent") not in CONTRACT_TYPES:
            raise ValueError(f"Contract type must be one of {sorted(CONTRACT_TYPES)}")
        if f.get("has_admin_rights") and f.get("contract_type") == "internship":
            raise ValueError("An intern cannot have admin rights")
        f.setdefault("salary", 0.0)
        return Employee(**f)


class OnboardingDirector:
    """Knows the standard onboarding recipes. Returns builders, so a preset can still be adjusted."""

    @staticmethod
    def developer(first_name: str, last_name: str, email: str, salary: float = 55_000) -> EmployeeBuilder:
        return (EmployeeBuilder()
                .with_name(first_name, last_name)
                .with_email(email)
                .with_job("Engineering", "Software Developer", salary)
                .with_equipment(laptop=True)
                .with_access(vpn=True, admin=True)
                .at_office("Paris - La Défense"))

    @staticmethod
    def intern(first_name: str, last_name: str, email: str, department: str) -> EmployeeBuilder:
        return (EmployeeBuilder()
                .with_name(first_name, last_name)
                .with_email(email)
                .with_job(department, "Intern", 14_400)
                .with_contract("internship")
                .with_equipment(laptop=True)
                .at_office("Paris - La Défense"))

    @staticmethod
    def manager(first_name: str, last_name: str, email: str, department: str, salary: float) -> EmployeeBuilder:
        return (EmployeeBuilder()
                .with_name(first_name, last_name)
                .with_email(email)
                .with_job(department, "Manager", salary)
                .with_equipment(laptop=True, parking=True)
                .with_access(vpn=True))


if __name__ == "__main__":
    # Fully custom employee: each value has a name, the order does not matter
    employee = (EmployeeBuilder()
                .with_name("John", "Doe")
                .with_email("John.Doe@company.com")
                .with_job("Engineering", "Senior Developer", 75_000)
                .starting_on("2024-01-15")
                .with_equipment(laptop=True, parking=False)
                .with_access(vpn=True, admin=True)
                .build())
    print(employee, "\n")

    # Presets from the director, one of them customised before building
    developer = OnboardingDirector.developer("Sofia", "Benali", "sofia.benali@company.com").build()
    intern = (OnboardingDirector.intern("Lucas", "Petit", "lucas.petit@company.com", "Marketing")
              .with_manager(42)
              .starting_on("2025-02-03")
              .build())
    for person in (developer, intern):
        print(f"{person.full_name:<14} {person.position:<20} laptop={person.has_laptop} "
              f"vpn={person.has_vpn_access} admin={person.has_admin_rights} contract={person.contract_type}")

    try:
        OnboardingDirector.intern("Eva", "Roux", "eva.roux@company.com", "IT").with_access(admin=True).build()
    except ValueError as error:
        print("\nRefused:", error)
