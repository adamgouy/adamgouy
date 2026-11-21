"""Singleton pattern - configuration manager.

Problems of the original code:
- every module (database, email, payment, app) opens and parses config.json again: the same file
  is read 4 times, which is wasted I/O;
- each module has its own copy of the settings: a change made by one module is invisible to the
  others, so the configuration can become inconsistent;
- there is no single place to replace the configuration in tests.

Solution: `ConfigManager` has only one instance in the whole program. The file is read the first
time the manager is created, and every later `ConfigManager()` returns that same object.
`__new__` is the method that creates the object (before `__init__`), so overriding it is the place
to return the existing instance. A lock makes the creation safe if two threads start at once.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).with_name("config.json")


class ConfigManager:
    _instance: ConfigManager | None = None
    _lock = threading.Lock()
    load_count = 0   # how many times a file was read (to show that it happens only once)

    def __new__(cls, path: str | Path = DEFAULT_PATH) -> ConfigManager:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:          # checked again inside the lock
                    instance = super().__new__(cls)
                    instance._load(Path(path))
                    cls._instance = instance
        return cls._instance

    @classmethod
    def get_instance(cls) -> ConfigManager:
        return cls()

    def _load(self, path: Path) -> None:
        with path.open(encoding="utf-8") as file:
            self._settings: dict = json.load(file)
        self.path = path
        ConfigManager.load_count += 1

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value with a dotted key: get("database.port") -> 5432."""
        node: Any = self._settings
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        """Change a value in memory: every module sees it, because they share the instance."""
        *parents, last = key.split(".")
        node = self._settings
        for part in parents:
            node = node.setdefault(part, {})
        node[last] = value

    def reload(self) -> None:
        """Read the file again (after it was edited on disk)."""
        self._load(self.path)

    @classmethod
    def _reset_for_tests(cls) -> None:
        cls._instance = None
        cls.load_count = 0


# --- The four "modules" of the original code, now sharing one configuration ---

def start_application() -> str:
    config = ConfigManager()
    return f"Starting {config.get('app.name')} v{config.get('app.version')} (debug={config.get('app.debug')})"


def connect_database() -> str:
    config = ConfigManager()
    return f"Connecting to {config.get('database.host')}:{config.get('database.port')}/{config.get('database.name')}"


def send_email(to: str, subject: str) -> str:
    config = ConfigManager()
    return f"Email '{subject}' to {to} from {config.get('email.sender')} via {config.get('email.smtp_host')}"


def process_payment(amount: float) -> str:
    config = ConfigManager()
    return (f"Charging {amount:.2f} {config.get('payment.currency')} with "
            f"{config.get('payment.provider')} ({config.get('payment.environment')})")


if __name__ == "__main__":
    print(start_application())
    print(connect_database())
    print(send_email("client@example.com", "Welcome"))
    print(process_payment(49.90))
    print("config.json was read", ConfigManager.load_count, "time(s)")
    print("Same object everywhere:", ConfigManager() is ConfigManager.get_instance())

    ConfigManager().set("app.debug", True)          # changed by one module...
    print("Seen by another module:", start_application())   # ...visible in all the others
