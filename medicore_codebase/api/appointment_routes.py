from services.appointment_service import AppointmentService

appointment_service = AppointmentService()


def book_appointment(patient_id, doctor_id, appointment_time):
    return appointment_service.book_appointment(
        patient_id,
        doctor_id,
        appointment_time,
    )


def get_patient_appointments(patient_id):
    return appointment_service.get_patient_appointments(patient_id)
