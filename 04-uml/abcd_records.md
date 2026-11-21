# Exercise 2 - ABCD Records (CD and tape mail-order company)

Exercise: https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb (slide 68) ·
Code: [`abcd_records.py`](abcd_records.py)

> Mermaid has no real use case diagram, so I draw them as flowcharts: actors are on the sides,
> use cases are the rounded boxes inside the **ABCD Records** frame (the system boundary), and
> dotted arrows are the `«include»` / `«extend»` relations.

## Level 1

### Task 1.1 - Simple use case diagram

```mermaid
flowchart LR
    member["👤 Member"]
    clerk["👤 Order processing clerk"]
    subgraph system["ABCD Records"]
        place(["Place an order"])
        pay(["Pay the order"])
        verify(["Verify membership"])
        process(["Process the order"])
    end
    member --- place
    member --- pay
    clerk --- verify
    clerk --- process
```

### Task 1.2 - Basic class diagram

```mermaid
classDiagram
    class Member {
        -member_id: str
        -name: str
        -address: str
        +place_order(items) Order
    }
    class Order {
        -order_id: int
        -order_date: date
        -items: list
        +total() float
    }
    class Item {
        -title: str
        -price: float
        -stock: int
    }
    class OrderProcessingClerk {
        -name: str
        +verify_membership(customer) bool
        +process(order)
    }
    Member "1" --> "0..*" Order : places
    Order "0..*" --> "1..*" Item : contains
    OrderProcessingClerk "1" --> "0..*" Order : processes
```

## Level 2

### Task 2.1 - Complete use case diagram

- **`«include»`** = always part of the base use case: placing an order always verifies the membership
  and the availability of the items; processing an order always prints the invoice and the shipping list.
- **`«extend»`** = only in some cases: the discount and the order of unavailable items only happen
  for Royal members; the membership application is only sent when the customer is not a member.

```mermaid
flowchart LR
    customer["👤 Customer"]
    member["👤 Member"]
    royal["👤 Royal member"]
    clerk["👤 Order processing clerk"]
    collection["👤 Collection dept. clerk"]
    subgraph system["ABCD Records"]
        place(["Place an order"])
        verify(["Verify membership"])
        availability(["Check item availability"])
        application(["Send membership application"])
        discount(["Apply Royal discount"])
        backorder(["Order unavailable item"])
        process(["Process the order"])
        invoice(["Print invoice"])
        shipping(["Print shipping list"])
        record(["Record in daily file"])
        pay(["Collect payment"])
    end
    royal -->|is a| member
    member -->|is a| customer
    customer --- place
    member --- pay
    clerk --- verify
    clerk --- process
    collection --- pay
    place -. "«include»" .-> verify
    place -. "«include»" .-> availability
    process -. "«include»" .-> invoice
    process -. "«include»" .-> shipping
    process -. "«include»" .-> record
    application -. "«extend»" .-> verify
    discount -. "«extend»" .-> place
    backorder -. "«extend»" .-> place
```

### Task 2.2 - Complete class diagram

Design choices:

- `Customer` is the parent of everybody who writes to the company. A `Member` has a member id;
  `RoyalMember` overrides two methods: `discount_rate()` (10%) and `can_backorder()` (True).
  This avoids `if member.type == "royal"` tests everywhere in the code.
- `Item` is abstract, `CD` and `Tape` add their own attributes.
- An `Order` is **composed** of `OrderLine`s (a line does not exist without its order); a line
  points to an `Item` and knows if it is backordered.
- The three payment types share the `PaymentMethod` interface (Strategy).

```mermaid
classDiagram
    class Customer {
        #name: str
        #address: str
    }
    class Member {
        -member_id: str
        +discount_rate() float
        +can_backorder() bool
    }
    class RoyalMember {
        +discount_rate() float
        +can_backorder() bool
    }
    class MembershipApplication {
        -sent_on: date
    }
    class Item {
        <<abstract>>
        #reference: str
        #title: str
        #price: float
        #stock: int
        +is_available(quantity) bool
        +remove_from_stock(quantity)
    }
    class CD {
        -artist: str
        -tracks: int
    }
    class Tape {
        -artist: str
        -length_min: int
    }
    class Order {
        -order_id: int
        -order_date: date
        -status: OrderStatus
        +add_line(item, quantity)
        +subtotal() float
        +discount() float
        +total() float
    }
    class OrderStatus {
        <<enumeration>>
        RECEIVED
        PROCESSED
        PAID
    }
    class OrderLine {
        -quantity: int
        -backordered: bool
        +amount() float
    }
    class Invoice {
        -amount: float
        -paid: bool
        +print() str
    }
    class ShippingList {
        +print() str
    }
    class PaymentMethod {
        <<interface>>
        +pay(amount)* str
    }
    class Cash
    class Check {
        -number: str
        -bank: str
    }
    class BankDraft {
        -number: str
    }
    class OrderProcessingClerk {
        +verify_membership(customer) bool
        +process(order) Invoice
    }
    class CollectionClerk {
        +collect(invoice, method) str
    }
    class DailyRecordFile {
        -day: date
        +record(order)
    }
    class Supplier {
        +reorder(item, quantity)
    }

    Customer <|-- Member
    Member <|-- RoyalMember
    Item <|-- CD
    Item <|-- Tape
    PaymentMethod <|.. Cash
    PaymentMethod <|.. Check
    PaymentMethod <|.. BankDraft

    Customer "1" --> "0..1" MembershipApplication : receives
    Member "1" --> "0..*" Order : places
    Order "1" *-- "1..*" OrderLine : contains
    Order --> OrderStatus
    OrderLine "0..*" --> "1" Item : refers to
    Order "1" --> "0..1" Invoice : billed by
    Order "1" --> "0..1" ShippingList : shipped with
    Invoice ..> PaymentMethod : paid with
    OrderProcessingClerk ..> Order : processes
    OrderProcessingClerk ..> Supplier : reorders from
    CollectionClerk ..> Invoice : collects
    DailyRecordFile "1" o-- "0..*" Order : records
```

#### Scenario that checks the diagram

A Royal member orders one CD in stock and one tape out of stock, and pays by check:

1. the clerk verifies the membership (OK) and the availability of each item;
2. the tape is not available, but a Royal member can backorder: the line is marked `backordered` and
   the tape is reordered from the supplier;
3. the 10% Royal discount is applied; the invoice shows the total, the shipping list contains only the CD;
4. the order is recorded in the daily file, and the collection clerk receives the check.

This scenario is the `__main__` of [`abcd_records.py`](abcd_records.py) and is also a test.

## Level 3 - Sequence diagrams

### 1. Complete order processing

```mermaid
sequenceDiagram
    actor M as Member
    actor OC as Order clerk
    participant O as Order
    participant I as Item
    participant F as DailyRecordFile
    M->>OC: order form (items, quantities)
    OC->>OC: verify_membership(member)
    OC->>O: create Order(member)
    loop each requested item
        OC->>I: is_available(quantity)
        I-->>OC: yes / no
        OC->>O: add_line(item, quantity)
    end
    OC->>O: total() with discount
    OC->>OC: print invoice and shipping list
    OC->>F: record(order)
    OC-->>M: invoice + parcel
```

### 2. Membership verification

```mermaid
sequenceDiagram
    actor C as Customer
    actor OC as Order clerk
    participant DB as Member list
    C->>OC: order form
    OC->>DB: find(customer)
    alt customer is a member
        DB-->>OC: Member
        OC-->>C: order accepted
    else customer is not a member
        DB-->>OC: not found
        OC->>OC: create MembershipApplication
        OC-->>C: order refused + membership application form
    end
```

### 3. Payment processing

```mermaid
sequenceDiagram
    actor M as Member
    actor CC as Collection clerk
    participant Inv as Invoice
    participant PM as PaymentMethod
    M->>CC: payment for invoice
    alt cash
        CC->>PM: Cash().pay(amount)
    else check
        CC->>PM: Check(number, bank).pay(amount)
    else bank draft
        CC->>PM: BankDraft(number).pay(amount)
    end
    PM-->>CC: receipt
    CC->>Inv: mark as paid
    CC-->>M: receipt
```

### 4. Reordering an item for a Royal member

```mermaid
sequenceDiagram
    actor R as Royal member
    actor OC as Order clerk
    participant I as Item
    participant S as Supplier
    R->>OC: order an item
    OC->>I: is_available(quantity)
    I-->>OC: no
    OC->>OC: member.can_backorder()? yes
    OC->>S: reorder(item, quantity)
    OC-->>R: line backordered, shipped later
    S-->>I: restock(quantity)
    OC-->>R: backordered item shipped
```
