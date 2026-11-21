# OOP & Design Patterns in Python - exercises

My solutions to the exercises of the **OOP & Design Patterns in Python** course
(course website: https://courses.dallard.tech/).

| Folder | Topic | Slide |
|---|---|---|
| [`01-bash`](01-bash) | Bash scripting: `env_install.sh` (Python + Jupyter setup, works on macOS, Linux and Windows/Git Bash) | 18 |
| [`02-git`](02-git) | Git mini exercise: commands of the 11 parts, install script, reflection questions | 26 |
| [`03-oop`](03-oop) | Operator overloading and inheritance | 67 |
| [`04-uml`](04-uml) | UML in Mermaid: hospital management system and ABCD Records, with a Python implementation | 68 |
| [`05-design-patterns`](05-design-patterns) | Factory, Builder, Singleton, Adapter, Decorator, Strategy, Template Method | 70-87 |
| [`06-testing`](06-testing) | Unit tests with mocks: Groq API and FastAPI app | 93 |

## Run the code

Requirements: Python 3.10+.

```bash
python -m pip install -r requirements.txt
python -m pytest
```

All the tests (97) run offline: the external API of exercise 6 is mocked, no API key is needed.
On Mac/Linux, use `python3` instead of `python`.

Each exercise can also be run on its own, for example:

```bash
python 03-oop/operator_overloading.py
python 05-design-patterns/creational/factory_payment.py
```

## How this repository was built

- **One branch per exercise** (`feature-bash`, `feature-git`, `feature-oop`, `feature-uml`,
  `feature-design-patterns`, `feature-testing`), merged into `main` when the exercise was finished.
  The merges are kept in the history: `git log --graph --oneline` shows the workflow.
- **Tests for every exercise**, run automatically by **GitHub Actions** on every push
  ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)): the green check next to a commit
  means all the tests passed.
- **No secrets in the repository**: API keys are read from environment variables and `.env` is ignored.
- `.gitattributes` keeps Unix line endings for the `.sh` scripts, so they still run on Mac/Linux
  after being committed from Windows.
