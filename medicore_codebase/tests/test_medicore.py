import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.patient_service import PatientService
from services.appointment_service import AppointmentService
from services.billing_service import BillingService
from middleware.auth import authenticate, authorize


def test_patient_registration():
    service = PatientService()

    patient = service.register_patient(
        "P001",
        "Test Patient",
        "1995-05-10",
        "9999999999",
    )

    assert patient.patient_id == "P001"
    assert service.get_patient("P001") is patient


def test_duplicate_patient_rejected():
    service = PatientService()

    service.register_patient(
        "P001",
        "Test Patient",
        "1995-05-10",
        "9999999999",
    )

    try:
        service.register_patient(
            "P001",
            "Another Patient",
            "1990-01-01",
            "8888888888",
        )
        assert False
    except ValueError:
        assert True


def test_double_booking_prevented():
    service = AppointmentService()

    service.book_appointment(
        "P001",
        "D001",
        "2026-10-01 10:00",
    )

    try:
        service.book_appointment(
            "P002",
            "D001",
            "2026-10-01 10:00",
        )
        assert False
    except ValueError:
        assert True


def test_billing_workflow():
    service = BillingService()

    invoice = service.create_invoice(
        "INV001",
        "P001",
        500,
    )

    assert invoice["status"] == "PENDING"

    paid = service.mark_paid("INV001")

    assert paid["status"] == "PAID"


def test_role_authorization():
    assert authenticate("doctor-token") == "doctor"
    assert authorize("doctor", "read") is True
    assert authorize("doctor", "delete") is False
