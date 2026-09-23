from api.patient_routes import register_patient, get_patient
from api.appointment_routes import book_appointment, get_patient_appointments
from api.billing_routes import create_invoice, mark_invoice_paid
from middleware.auth import authenticate, authorize


def create_patient_record(patient_id, name, date_of_birth, phone):
    return register_patient(
        patient_id,
        name,
        date_of_birth,
        phone,
    )


def schedule_patient_appointment(patient_id, doctor_id, appointment_time):
    return book_appointment(
        patient_id,
        doctor_id,
        appointment_time,
    )


def create_patient_invoice(invoice_id, patient_id, amount):
    return create_invoice(
        invoice_id,
        patient_id,
        amount,
    )


def process_request(token, permission):
    role = authenticate(token)

    if role is None:
        return False

    return authorize(role, permission)
