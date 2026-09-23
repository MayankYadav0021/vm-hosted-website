from services.patient_service import PatientService

patient_service = PatientService()


def register_patient(patient_id, name, date_of_birth, phone):
    return patient_service.register_patient(
        patient_id,
        name,
        date_of_birth,
        phone,
    )


def get_patient(patient_id):
    return patient_service.get_patient(patient_id)
