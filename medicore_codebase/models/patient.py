class Patient:
    def __init__(self, patient_id, name, date_of_birth, phone):
        self.patient_id = patient_id
        self.name = name
        self.date_of_birth = date_of_birth
        self.phone = phone

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "date_of_birth": self.date_of_birth,
            "phone": self.phone,
        }
