"""Template Method pattern - ETL data pipelines.

Answers to the questions about the original code:
1. The validation code is copied in the 3 pipelines; only the list of required keys changes.
2. The cleanup code is copied 3 times, identically.
3. To add logging, you would have to edit the 3 classes (and keep them consistent).
4. To change the order of the steps, you must edit 3 `run()` methods, and forgetting one creates a
   pipeline that behaves differently from the others.
5. Roughly two thirds of each class is duplicated (connect, validate, load, cleanup).

Solution: the parent class `DataPipeline` defines the algorithm ONCE in `run()` (the template
method). The steps that are the same everywhere are implemented in the parent; the steps that
change (`extract`, `transform`) are abstract and written by each subclass. Optional "hooks"
(`before_run`, `after_run`) do nothing by default and can be overridden.
Logging is now added in one place (`_step`) and every pipeline gets it.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod


class DataPipeline(ABC):
    source_type = "generic"
    required_keys: tuple[str, ...] = ()
    latency = 0.3          # simulated network / disk time, in seconds (0 in the tests)

    def __init__(self, source: str):
        self.source = source
        self.data: list[dict] = []
        self.log: list[str] = []

    # ---------------- the template method: same algorithm for everybody ----------------
    def run(self) -> list[dict]:
        self.before_run()
        self._step("connect", self.connect)
        self.data = self._step("extract", self.extract)
        self.data = self._step("transform", lambda: self.transform(self.data))
        self._step("validate", self.validate)
        loaded = self._step("load", self.load)
        self._step("cleanup", self.cleanup)
        self.after_run()
        return loaded

    def _step(self, name: str, action):
        start = time.perf_counter()
        result = action()
        message = f"[{self.source_type}] {name:<9} done in {time.perf_counter() - start:.2f}s"
        self.log.append(message)
        print(message)
        return result

    # ---------------- steps that change: each subclass MUST write them ----------------
    @abstractmethod
    def extract(self) -> list[dict]: ...

    @abstractmethod
    def transform(self, data: list[dict]) -> list[dict]: ...

    # ---------------- common steps: written once ----------------
    def connect(self) -> None:
        time.sleep(self.latency)

    def validate(self) -> None:
        for index, record in enumerate(self.data):
            missing = [key for key in self.required_keys if key not in record]
            if missing:
                raise ValueError(f"Record {index} is missing {missing}")

    def load(self) -> list[dict]:
        time.sleep(self.latency)
        return list(self.data)

    def cleanup(self) -> None:
        self.data = []

    # ---------------- hooks: optional, empty by default ----------------
    def before_run(self) -> None:
        pass

    def after_run(self) -> None:
        pass


class CSVPipeline(DataPipeline):
    source_type = "CSV"
    required_keys = ("id", "name", "age")

    def extract(self) -> list[dict]:
        return [{"id": "1", "name": "alice", "age": "30"}, {"id": "2", "name": "bob", "age": "25"}]

    def transform(self, data: list[dict]) -> list[dict]:
        return [{"id": int(r["id"]), "name": r["name"].title(), "age": int(r["age"])} for r in data]


class APIPipeline(DataPipeline):
    source_type = "API"
    required_keys = ("user_id", "username", "score")

    def extract(self) -> list[dict]:
        return [{"user_id": 101, "username": "Charlie", "score": "85"},
                {"user_id": 102, "username": "Diana", "score": "92"}]

    def transform(self, data: list[dict]) -> list[dict]:
        result = []
        for r in data:
            score = int(r["score"])
            result.append({**r, "username": r["username"].lower(), "score": score,
                           "grade": "A" if score >= 90 else "B"})
        return result


class DatabasePipeline(DataPipeline):
    source_type = "Database"
    required_keys = ("product_id", "name", "price")
    VAT = 0.20

    def extract(self) -> list[dict]:
        return [{"product_id": 501, "name": "laptop", "price": "1200"},
                {"product_id": 502, "name": "mouse", "price": "25"}]

    def transform(self, data: list[dict]) -> list[dict]:
        return [{**r, "name": r["name"].capitalize(), "price": float(r["price"]),
                 "price_incl_vat": round(float(r["price"]) * (1 + self.VAT), 2)} for r in data]


# --- Validation of the design: a new pipeline, nothing else was modified ---

class JSONFilePipeline(DataPipeline):
    source_type = "JSON"
    required_keys = ("order_id", "amount")
    SAMPLE = '[{"order_id": "A-1", "amount": "59.90", "paid": "yes"}, {"order_id": "A-2", "amount": "15", "paid": "no"}]'

    def extract(self) -> list[dict]:
        return json.loads(self.SAMPLE)

    def transform(self, data: list[dict]) -> list[dict]:
        return [{"order_id": r["order_id"], "amount": float(r["amount"]), "paid": r["paid"] == "yes"}
                for r in data]

    def after_run(self) -> None:       # uses a hook
        print(f"[{self.source_type}] archived {self.source}")


if __name__ == "__main__":
    pipelines = [
        CSVPipeline("data/users.csv"),
        APIPipeline("https://api.example.com/users"),
        DatabasePipeline("postgresql://localhost/shop"),
        JSONFilePipeline("data/orders.json"),
    ]
    for pipeline in pipelines:
        print(f"\n===== {pipeline.source_type} pipeline =====")
        for record in pipeline.run():
            print("   ", record)
