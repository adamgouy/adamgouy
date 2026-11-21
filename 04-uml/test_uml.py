"""Tests for the UML exercises: the code must behave like the diagrams say."""
import pytest

import abcd_records as abcd
import hospital as h


# ---------------------------------------------------------------------------
# Hospital
# ---------------------------------------------------------------------------

@pytest.fixture
def hospital():
    system = h.HospitalSystem()
    organizer = h.Organizer("Nadia", "org-pass")
    doctor = h.Doctor("Dr Martin", "doc-pass", "neurology")
    patient = h.Patient("Hugo", "hugo-pass")
    for member in (organizer, doctor, patient):
        system.register(member)
    return system, organizer, doctor, patient


def test_registration_gives_ids_and_login_checks_the_password(hospital):
    system, organizer, doctor, patient = hospital
    assert patient.member_id.startswith("PAT-") and doctor.member_id.startswith("DOC-")
    assert system.login(patient.member_id, "hugo-pass") is patient
    with pytest.raises(PermissionError):
        system.login(patient.member_id, "wrong")


def test_password_is_not_stored_in_clear(hospital):
    _, _, _, patient = hospital
    assert "hugo-pass" not in vars(patient).values()


def test_full_consultation_and_payment(hospital):
    _, organizer, doctor, patient = hospital
    problem = patient.post_problem("Back pain")
    assert problem.status is h.ProblemStatus.SUBMITTED

    organizer.assign(problem, doctor)
    doctor.prescribe(problem, "Physiotherapy", fee=60)
    prescription = organizer.deliver_prescription(problem)
    payment = patient.pay(prescription, h.CashPayment())
    organizer.forward_payment(payment)

    assert problem.status is h.ProblemStatus.CLOSED
    assert payment.status is h.PaymentStatus.FORWARDED
    assert doctor.earnings == 60
    assert patient.prescriptions() == [prescription]


def test_only_the_assigned_doctor_can_prescribe(hospital):
    _, organizer, doctor, patient = hospital
    other = h.Doctor("Dr Lee", "pass", "cardiology")
    problem = patient.post_problem("Chest pain")
    organizer.assign(problem, doctor)
    with pytest.raises(PermissionError):
        other.prescribe(problem, "Rest", fee=30)


def test_a_payment_cannot_be_forwarded_twice(hospital):
    _, organizer, doctor, patient = hospital
    problem = patient.post_problem("Fever")
    organizer.assign(problem, doctor)
    doctor.prescribe(problem, "Rest", fee=30)
    payment = patient.pay(problem.prescription, h.CheckPayment("123", "BNP"))
    organizer.forward_payment(payment)
    with pytest.raises(ValueError):
        organizer.forward_payment(payment)
    assert doctor.earnings == 30


def test_a_prescription_cannot_be_paid_twice(hospital):
    _, organizer, doctor, patient = hospital
    problem = patient.post_problem("Fever")
    organizer.assign(problem, doctor)
    prescription = doctor.prescribe(problem, "Rest", fee=30)
    patient.pay(prescription, h.CashPayment())
    with pytest.raises(ValueError):
        patient.pay(prescription, h.CashPayment())


def test_renewed_prescription_keeps_the_history(hospital):
    _, organizer, doctor, patient = hospital
    problem = patient.post_problem("Allergy")
    organizer.assign(problem, doctor)
    first = doctor.prescribe(problem, "Antihistamine", fee=25)
    renewal = first.renew()
    assert renewal.renewal_of is first and renewal.treatment == first.treatment


def test_credit_card_keeps_only_the_last_digits():
    card = h.CreditCardPayment("4970 1234 5678 9012")
    assert card.pay(10).endswith("10.00 EUR") and "1234" not in card.pay(10)
    with pytest.raises(ValueError):
        h.CreditCardPayment("1234")


# ---------------------------------------------------------------------------
# ABCD Records
# ---------------------------------------------------------------------------

@pytest.fixture
def shop():
    royal = abcd.RoyalMember("M-1", "Ines", "Lyon")
    regular = abcd.Member("M-2", "Leo", "Nantes")
    supplier, records = abcd.Supplier(), abcd.DailyRecordFile()
    clerk = abcd.OrderProcessingClerk({"M-1": royal, "M-2": regular}, supplier, records)
    cd = abcd.CD("CD-1", "Album A", 20.0, stock=5, artist="X", tracks=10)
    tape = abcd.Tape("TP-1", "Album B", 10.0, stock=0, artist="Y", length_min=40)
    return clerk, supplier, records, royal, regular, cd, tape


def test_royal_member_scenario(shop):
    clerk, supplier, records, royal, _, cd, tape = shop
    order = clerk.place_order(royal, [(cd, 2), (tape, 1)])
    invoice, shipping = clerk.process(order)

    assert [line.backordered for line in order.lines] == [False, True]
    assert order.subtotal() == 50 and order.discount() == 5 and invoice.amount == 45
    assert [line.item for line in shipping.lines] == [cd]          # the tape ships later
    assert supplier.pending == [(tape, 1)]
    assert records.orders == [order]
    assert cd.stock == 3

    receipt = abcd.CollectionClerk().collect(invoice, abcd.Check("42", "LCL"))
    assert "45.00" in receipt and invoice.paid and order.status is abcd.OrderStatus.PAID


def test_regular_member_gets_no_discount_and_cannot_backorder(shop):
    clerk, supplier, _, _, regular, cd, tape = shop
    order = clerk.place_order(regular, [(cd, 1), (tape, 1)])
    assert [line.item for line in order.lines] == [cd]
    assert order.total() == 20
    assert supplier.pending == []


def test_non_member_receives_an_application(shop):
    clerk, *_, cd, _ = shop
    with pytest.raises(abcd.NotAMemberError) as error:
        clerk.place_order(abcd.Customer("Paul", "Paris"), [(cd, 1)])
    assert isinstance(error.value.application, abcd.MembershipApplication)


@pytest.mark.parametrize("method", [abcd.Cash(), abcd.Check("1", "LCL"), abcd.BankDraft("9")])
def test_every_payment_method_works(shop, method):
    clerk, _, _, royal, _, cd, _ = shop
    invoice, _ = clerk.process(clerk.place_order(royal, [(cd, 1)]))
    assert "18.00" in abcd.CollectionClerk().collect(invoice, method)


def test_supplier_delivery_restocks_the_item(shop):
    clerk, supplier, _, royal, _, _, tape = shop
    clerk.place_order(royal, [(tape, 2)])
    supplier.deliver_all()
    assert tape.stock == 2 and supplier.pending == []
