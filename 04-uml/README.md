# 04 - UML

Exercise: https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb (slide 68)

The diagrams are written in **Mermaid** inside the Markdown files: GitHub draws them automatically,
and they are versioned like code (a change in a diagram is visible in `git diff`).

| Exercise | Diagrams | Code |
|---|---|---|
| 1 - Online hospital management | [`hospital.md`](hospital.md): basic and detailed class diagrams, sequence and system sequence diagrams, answers to the questions | [`hospital.py`](hospital.py) |
| 2 - ABCD Records | [`abcd_records.md`](abcd_records.md): use case diagrams (simple and with `«include»` / `«extend»`), class diagrams, 4 sequence diagrams | [`abcd_records.py`](abcd_records.py) |

To check that the diagrams are consistent, I implemented them in Python and wrote tests
([`test_uml.py`](test_uml.py)) that replay the scenarios of the sequence diagrams.

```bash
python hospital.py
python abcd_records.py
python -m pytest      # from the repository root
```

## UML notation reminder

| Relation | Mermaid | Meaning |
|---|---|---|
| Inheritance | `A <\|-- B` | B *is a* A |
| Interface implementation | `A <\|.. B` | B implements the interface A |
| Composition | `A *-- B` | B is part of A and cannot exist without it |
| Aggregation | `A o-- B` | A contains B, but B can exist alone |
| Association | `A --> B` | A knows / uses B for a long time |
| Dependency | `A ..> B` | A uses B temporarily (parameter, local variable) |
| Visibility | `+` public, `-` private, `#` protected | |
