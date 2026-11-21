"""Tests for the 7 design patterns. Run from the repository root with: python -m pytest"""
import json
import threading

import pytest

from behavioral.strategy_report import (
    CSVFormatStrategy, FormatStrategy, HTMLFormatStrategy, JSONFormatStrategy,
    MarkdownFormatStrategy, PDFFormatStrategy, ReportGenerator,
)
from behavioral.template_etl import (
    APIPipeline, CSVPipeline, DatabasePipeline, DataPipeline, JSONFilePipeline,
)
from creational.builder_employee import EmployeeBuilder, OnboardingDirector
from creational.factory_payment import PaymentFactory, PaymentProcessor
from creational.singleton_config import ConfigManager, connect_database, start_application
from structural.adapter_report import (
    JSONReportSource, LegacyReportAdapter, LegacyReportGenerator, NativeJSONReportGenerator,
)
from structural.decorator_order import (
    BaseOrder, DiscountDecorator, ExpressShippingDecorator, GiftWrapDecorator,
    InsuranceDecorator, PremiumMemberDecorator,
)


# ------------------------------------------------------------------ Factory

@pytest.mark.parametrize("method, details, total, fee", [
    ("credit_card", {"card_number": "4970123456789012", "cvv": "123"}, 102.90, 2.90),
    ("bank_transfer", {"iban": "FR7630006000011234567890189"}, 101.50, 1.50),
    ("paypal", {"email": "anna@example.com"}, 103.70, 3.70),
    ("apple_pay", {"device_token": "tok"}, 102.00, 2.00),
])
def test_factory_creates_the_right_processor(method, details, total, fee):
    result = PaymentFactory().get_processor(method).process(100, details)
    assert result == {"success": True, "method": method, "amount": total, "fee": fee}


@pytest.mark.parametrize("method, details", [
    ("credit_card", {"card_number": "1234", "cvv": "123"}),
    ("bank_transfer", {"iban": "123"}),
    ("paypal", {"email": "no-at-sign"}),
    ("apple_pay", {}),
])
def test_invalid_details_are_refused(method, details):
    result = PaymentFactory().get_processor(method).process(100, details)
    assert result["success"] is False and result["error"]


def test_unknown_method_raises():
    with pytest.raises(ValueError, match="Available"):
        PaymentFactory().get_processor("bitcoin")


def test_new_method_can_be_added_without_modifying_the_factory():
    @PaymentFactory.register("voucher")
    class VoucherProcessor(PaymentProcessor):
        def validate(self, details):
            return None if details.get("code") else "Missing code"

        def compute_fee(self, amount):
            return 0

    try:
        assert PaymentFactory().get_processor("voucher").process(20, {"code": "X"})["amount"] == 20
    finally:
        PaymentFactory._registry.pop("voucher")


# ------------------------------------------------------------------ Builder

def test_builder_with_chained_calls():
    employee = (EmployeeBuilder().with_name("John", "Doe").with_email("John.Doe@company.com")
                .with_job("Engineering", "Developer", 70_000).starting_on("2024-01-15")
                .with_equipment(laptop=True).with_access(vpn=True).build())
    assert employee.full_name == "John Doe"
    assert employee.email == "john.doe@company.com"
    assert employee.start_date.isoformat() == "2024-01-15"
    assert employee.has_laptop and employee.has_vpn_access and not employee.has_admin_rights


@pytest.mark.parametrize("broken_builder", [
    lambda: EmployeeBuilder().with_email("a@b.com").with_job("IT", "Dev", 1),            # no name
    lambda: EmployeeBuilder().with_name("A", "B").with_email("wrong").with_job("IT", "Dev", 1),
    lambda: EmployeeBuilder().with_name("A", "B").with_email("a@b.com").with_job("IT", "Dev", -5),
    lambda: EmployeeBuilder().with_name("A", "B").with_email("a@b.com").with_job("IT", "Dev", 1)
                             .with_contract("forever"),
])
def test_build_validates_everything(broken_builder):
    with pytest.raises(ValueError):
        broken_builder().build()


def test_director_presets():
    developer = OnboardingDirector.developer("Sofia", "Benali", "sofia@company.com").build()
    intern = OnboardingDirector.intern("Lucas", "Petit", "lucas@company.com", "Marketing").build()
    assert developer.has_laptop and developer.has_vpn_access and developer.has_admin_rights
    assert intern.contract_type == "internship" and not intern.has_admin_rights


def test_a_preset_can_be_customised_but_rules_still_apply():
    intern = OnboardingDirector.intern("L", "P", "l@company.com", "IT").with_manager(7).build()
    assert intern.manager_id == 7
    with pytest.raises(ValueError, match="intern"):
        OnboardingDirector.intern("L", "P", "l@company.com", "IT").with_access(admin=True).build()


def test_built_employee_cannot_be_modified():
    employee = OnboardingDirector.developer("Sofia", "Benali", "sofia@company.com").build()
    with pytest.raises(AttributeError):
        employee.salary = 1


# ------------------------------------------------------------------ Singleton

@pytest.fixture
def fresh_config():
    ConfigManager._reset_for_tests()
    yield
    ConfigManager._reset_for_tests()


def test_singleton_returns_the_same_instance(fresh_config):
    assert ConfigManager() is ConfigManager() is ConfigManager.get_instance()


def test_config_file_is_read_only_once(fresh_config):
    start_application()
    connect_database()
    ConfigManager()
    assert ConfigManager.load_count == 1


def test_dotted_keys(fresh_config):
    config = ConfigManager()
    assert config.get("database.port") == 5432
    assert config.get("database.missing", "default") == "default"


def test_a_change_is_seen_everywhere(fresh_config):
    ConfigManager().set("app.name", "TestApp")
    assert "TestApp" in start_application()


def test_singleton_is_thread_safe(fresh_config):
    instances = []
    threads = [threading.Thread(target=lambda: instances.append(ConfigManager())) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len({id(instance) for instance in instances}) == 1
    assert ConfigManager.load_count == 1


# ------------------------------------------------------------------ Adapter

def test_adapter_really_converts_the_xml():
    data = {"total_sales": 150000, "avg_order": 121.56, "region": "EMEA", "closed": True}
    adapter = LegacyReportAdapter(LegacyReportGenerator())
    assert isinstance(adapter, JSONReportSource)
    assert json.loads(adapter.generate(data)) == data      # types are restored


def test_adapter_and_native_generator_are_interchangeable():
    data = {"orders": 12, "low_stock": 3}
    legacy = LegacyReportAdapter(LegacyReportGenerator()).generate(data)
    native = NativeJSONReportGenerator().generate(data)
    assert json.loads(legacy) == json.loads(native)


def test_adapter_calls_the_legacy_system(mocker):
    legacy = LegacyReportGenerator()
    spy = mocker.spy(legacy, "generate_report")
    LegacyReportAdapter(legacy).generate({"a": 1})
    spy.assert_called_once_with({"a": 1})


# ------------------------------------------------------------------ Decorator

def test_base_order():
    assert BaseOrder(100).get_cost() == 100


def test_each_option():
    assert ExpressShippingDecorator(BaseOrder(100)).get_cost() == 115
    assert InsuranceDecorator(BaseOrder(100)).get_cost() == 105
    assert GiftWrapDecorator(BaseOrder(100)).get_cost() == 105
    assert DiscountDecorator(BaseOrder(100), 20).get_cost() == 80
    assert PremiumMemberDecorator(BaseOrder(100)).get_cost() == 90


def test_stacked_options():
    order = PremiumMemberDecorator(DiscountDecorator(GiftWrapDecorator(
        ExpressShippingDecorator(InsuranceDecorator(BaseOrder(100)))), percent=15))
    assert order.get_cost() == 95.63
    description = order.get_description()
    assert description.index("Insurance") < description.index("Express") < description.index("Premium")


def test_the_order_of_decorators_matters():
    discount_last = DiscountDecorator(ExpressShippingDecorator(BaseOrder(100)), 10)
    discount_first = ExpressShippingDecorator(DiscountDecorator(BaseOrder(100), 10))
    assert discount_last.get_cost() == 103.5 and discount_first.get_cost() == 105


def test_invalid_discount():
    with pytest.raises(ValueError):
        DiscountDecorator(BaseOrder(100), 150)


# ------------------------------------------------------------------ Strategy

SALES = [{"name": "Q1", "value": 15000}, {"name": "Q2", "value": 18000}]


@pytest.mark.parametrize("strategy, expected", [
    (CSVFormatStrategy(), "name,value\nQ1,15000\nQ2,18000"),
    (MarkdownFormatStrategy(), "| Name | Value |\n|---|---:|\n| Q1 | 15000 |\n| Q2 | 18000 |"),
])
def test_text_formats(strategy, expected):
    assert ReportGenerator(SALES, strategy).generate_report() == expected


def test_json_and_html_formats():
    assert json.loads(ReportGenerator(SALES, JSONFormatStrategy()).generate_report()) == SALES
    html = ReportGenerator([{"name": "<b>", "value": 1}], HTMLFormatStrategy()).generate_report()
    assert "&lt;b&gt;" in html                   # names are escaped


def test_strategy_can_change_at_runtime():
    generator = ReportGenerator(SALES, PDFFormatStrategy())
    assert generator.generate_report().startswith("PDF REPORT")
    generator.set_strategy(CSVFormatStrategy())
    assert generator.generate_report().startswith("name,value")


def test_no_strategy_raises():
    with pytest.raises(ValueError):
        ReportGenerator(SALES).generate_report()


def test_save_uses_the_strategy_extension(tmp_path):
    path = ReportGenerator(SALES, CSVFormatStrategy()).save_report(tmp_path / "report")
    assert path.name == "report.csv" and path.read_text().startswith("name,value")


def test_a_new_format_needs_no_change_in_existing_classes():
    class UpperStrategy(FormatStrategy):
        extension = "txt"

        def format(self, data):
            return " ".join(item["name"].upper() for item in data)

    assert ReportGenerator([{"name": "q1", "value": 1}], UpperStrategy()).generate_report() == "Q1"


# ------------------------------------------------------------------ Template Method

@pytest.fixture(autouse=True)
def no_latency(monkeypatch):
    monkeypatch.setattr(DataPipeline, "latency", 0)


@pytest.mark.parametrize("pipeline_cls, first", [
    (CSVPipeline, {"id": 1, "name": "Alice", "age": 30}),
    (APIPipeline, {"user_id": 101, "username": "charlie", "score": 85, "grade": "B"}),
    (DatabasePipeline, {"product_id": 501, "name": "Laptop", "price": 1200.0, "price_incl_vat": 1440.0}),
    (JSONFilePipeline, {"order_id": "A-1", "amount": 59.9, "paid": True}),
])
def test_pipelines(pipeline_cls, first):
    assert pipeline_cls("source").run()[0] == first


def test_steps_always_run_in_the_same_order():
    pipeline = CSVPipeline("users.csv")
    pipeline.run()
    steps = [line.split()[1] for line in pipeline.log]
    assert steps == ["connect", "extract", "transform", "validate", "load", "cleanup"]
    assert pipeline.data == []                 # cleanup ran


def test_validation_is_shared():
    class BrokenPipeline(CSVPipeline):
        def transform(self, data):
            return [{"id": 1}]                 # "name" and "age" are missing

    with pytest.raises(ValueError, match="missing"):
        BrokenPipeline("broken.csv").run()


def test_hook_is_called(capsys):
    JSONFilePipeline("orders.json").run()
    assert "archived orders.json" in capsys.readouterr().out


def test_the_template_cannot_be_instantiated_without_the_steps():
    with pytest.raises(TypeError):
        DataPipeline("x")
