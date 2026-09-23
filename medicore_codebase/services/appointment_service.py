class AppointmentService:
    def __init__(self):
        self.appointments = []

    def book_appointment(self, patient_id, doctor_id, appointment_time):
        for appointment in self.appointments:
            if (
                appointment["doctor_id"] == doctor_id
                and appointment["appointment_time"] == appointment_time
            ):
                raise ValueError("Doctor already has an appointment at this time")

        appointment = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_time": appointment_time,
        }

        self.appointments.append(appointment)
        return appointment

    def get_patient_appointments(self, patient_id):
        return [
            appointment
            for appointment in self.appointments
            if appointment["patient_id"] == patient_id
        ]
