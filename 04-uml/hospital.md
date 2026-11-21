# Exercise 1 - Online hospital management system

Exercise: https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb (slide 68) ·
Code: [`hospital.py`](hospital.py)

All diagrams are written in [Mermaid](https://mermaid.js.org/), so GitHub draws them directly.

## Task 1 - Basic class diagram

The three actors of the statement and what each of them does.

```mermaid
classDiagram
    class Patient {
        -member_id: str
        -name: str
        -password: str
        +post_problem(description)
        +pay(prescription, method)
    }
    class Organizer {
        -member_id: str
        -name: str
        -password: str
        +register_member()
        +assign(problem, doctor)
        +deliver_prescription(problem)
        +forward_payment(payment)
    }
    class Doctor {
        -member_id: str
        -name: str
        -password: str
        -speciality: str
        +prescribe(problem)
    }
    Patient "0..*" --> "1" Organizer : sends problems to
    Organizer "1" --> "0..*" Doctor : consults
    Doctor "1" --> "0..*" Patient : prescribes for
```

## Task 2 - Detailed class diagram

Design choices:

- **`Member`** is an abstract parent class: the three roles share an id, a name and a password,
  so these attributes and `check_password()` are written once. The password is stored as a hash.
- **`HealthProblem`** is the central object: it links a patient, the doctor in charge and the
  prescription, and its `ProblemStatus` follows the life cycle `SUBMITTED → ASSIGNED → PRESCRIBED → CLOSED`.
- **Composition** `HealthProblem *-- Prescription`: a prescription has no meaning without the problem
  it answers, it is created by the problem's doctor and dies with it.
- **Aggregation** `Patient o-- HealthProblem`: the patient keeps the history of his problems.
- **`PaymentMethod`** is an interface with three implementations (cash, check, credit card). A
  `Payment` *uses* a method instead of being subclassed: this is the **Strategy** pattern.
- **`PaymentStatus`** (`RECEIVED → FORWARDED`) prevents a payment from being forwarded twice.

```mermaid
classDiagram
    class Member {
        <<abstract>>
        #member_id: str
        #name: str
        -password_hash: str
        +check_password(password) bool
        +role()* str
    }
    class Patient {
        -problems: list~HealthProblem~
        +post_problem(description) HealthProblem
        +pay(prescription, method) Payment
        +prescriptions() list~Prescription~
    }
    class Doctor {
        -speciality: str
        -earnings: float
        +prescribe(problem, treatment, fee) Prescription
        +receive(amount)
    }
    class Organizer {
        +assign(problem, doctor)
        +deliver_prescription(problem) Prescription
        +forward_payment(payment)
    }
    class HospitalSystem {
        -members: dict
        -problems: list~HealthProblem~
        +register(member) str
        +login(member_id, password) Member
    }
    class HealthProblem {
        -problem_id: int
        -description: str
        -status: ProblemStatus
        -created_at: datetime
    }
    class ProblemStatus {
        <<enumeration>>
        SUBMITTED
        ASSIGNED
        PRESCRIBED
        CLOSED
    }
    class Prescription {
        -treatment: str
        -fee: float
        -issued_at: datetime
        -renewal_of: Prescription
        +renew() Prescription
    }
    class Payment {
        -amount: float
        -status: PaymentStatus
        -receipt: str
    }
    class PaymentStatus {
        <<enumeration>>
        RECEIVED
        FORWARDED
    }
    class PaymentMethod {
        <<interface>>
        +pay(amount)* str
    }
    class CashPayment
    class CheckPayment {
        -check_number: str
        -bank: str
    }
    class CreditCardPayment {
        -card_number: str
        +pay(amount) str
    }

    Member <|-- Patient
    Member <|-- Doctor
    Member <|-- Organizer
    PaymentMethod <|.. CashPayment
    PaymentMethod <|.. CheckPayment
    PaymentMethod <|.. CreditCardPayment

    HospitalSystem "1" o-- "0..*" Member : registers
    Patient "1" o-- "0..*" HealthProblem : posts
    HealthProblem "0..*" --> "0..1" Doctor : assigned to
    HealthProblem "1" *-- "0..1" Prescription : answered by
    HealthProblem --> ProblemStatus
    Prescription "0..1" --> "0..1" Prescription : renewal of
    Payment "0..1" --> "1" Prescription : settles
    Payment --> "1" PaymentMethod : paid with
    Payment --> PaymentStatus
```

### Sequence diagram - from a problem to a paid prescription

```mermaid
sequenceDiagram
    actor P as Patient
    actor O as Organizer
    actor D as Doctor
    P->>O: post_problem("strong headache")
    O->>D: assign(problem, doctor)
    D->>D: prescribe(problem, treatment, fee)
    D-->>O: prescription
    O->>P: deliver_prescription(problem)
    P->>O: pay(prescription, CreditCardPayment)
    O->>D: forward_payment(payment)
    Note over P,D: problem status: CLOSED
```

## Task 3 - System sequence diagrams

The system is a black box: these diagrams only show the messages between the actors and the system.

### 1. Registration of a new patient

```mermaid
sequenceDiagram
    actor O as Organizer
    participant S as HospitalSystem
    actor P as New patient
    O->>S: login(organizer_id, password)
    S-->>O: access granted
    O->>S: register(Patient(name, password))
    S->>S: create member id, hash the password
    S-->>O: member_id
    O-->>P: member id + password
    P->>S: login(member_id, password)
    S-->>P: welcome
```

### 2. Consultation

```mermaid
sequenceDiagram
    actor P as Patient
    participant S as HospitalSystem
    actor O as Organizer
    actor D as Doctor
    P->>S: post_problem(description)
    S-->>O: new problem (SUBMITTED)
    O->>S: assign(problem, doctor)
    S-->>D: problem to examine (ASSIGNED)
    D->>S: prescribe(problem, treatment, fee)
    S-->>O: prescription ready (PRESCRIBED)
    O->>S: deliver_prescription(problem)
    S-->>P: prescription
```

### 3. Payment

```mermaid
sequenceDiagram
    actor P as Patient
    participant S as HospitalSystem
    actor O as Organizer
    actor D as Doctor
    P->>S: pay(prescription, method)
    alt amount and method valid
        S->>S: method.pay(fee) → receipt
        S-->>P: receipt, problem CLOSED
        O->>S: forward_payment(payment)
        S->>D: receive(fee)
        S->>S: payment.status = FORWARDED
    else invalid payment
        S-->>P: error, nothing is recorded
    end
```

## Questions

**1. How can a patient consult several doctors?**
Each `HealthProblem` has its own doctor, so a patient with several problems already sees several
doctors. If one problem needs several doctors (a second opinion, a specialist), the link
`HealthProblem → Doctor` can become `0..*`, or better an association class `Consultation`
(problem, doctor, date, notes) between the two.

**2. How can prescriptions be reused?**
A renewal is a new `Prescription` that points to the previous one (`renewal_of`). The history is
kept, each renewal has its own date and fee, and the original prescription is never modified.

**3. Which design pattern fits the payment?**
**Strategy**: the three payment methods share the `PaymentMethod` interface and the rest of the
system calls `method.pay(amount)` without knowing which one it is. Adding a new method (bank
transfer, mobile payment) does not change any existing class. A **Factory** can be added to create
the right method from the patient's choice.

**4. How to guarantee the integrity of payments?**
- the amount must be equal to the prescription fee, and a prescription can only be paid once;
- a payment is forwarded only if its status is `RECEIVED`, then it becomes `FORWARDED`: it can never
  be forwarded twice;
- in a real system, "record the payment" and "credit the doctor" are done in one **database
  transaction**: both succeed or both are cancelled;
- each payment keeps its receipt and date (audit trail), and card numbers are never stored in full.
