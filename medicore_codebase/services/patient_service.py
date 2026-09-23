from models.patient import Patient


class PatientService:
    def __init__(self):
        self.patients = {}

    def register_patient(self, patient_id, name, date_of_birth, phone):
        if patient_id in self.patients:
            raise ValueError("Patient already exists")

        patient = Patient(
            patient_id=patient_id,
            name=name,
            date_of_birth=date_of_birth,
            phone=phone,
        )

        self.patients[patient_id] = patient
        return patient

    def get_patient(self, patient_id):
        return self.patients.get(patient_id)
