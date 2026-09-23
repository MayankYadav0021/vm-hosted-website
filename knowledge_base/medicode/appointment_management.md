# MediCore Systems - Appointment Management

## Overview

The Appointment Management module handles the creation, scheduling, modification, cancellation, and retrieval of patient appointments.

It works with the Patient Management module and uses the patient ID to associate appointments with patient records.

## Appointment Creation

An authorized user can create an appointment by providing:

- Patient ID
- Doctor ID
- Appointment date
- Appointment time
- Appointment type

Before creating an appointment, the system validates the patient ID and checks whether the requested appointment slot is available.

## Appointment Scheduling

The system must prevent conflicting appointments for the same doctor and time slot.

A simplified workflow is:

1. Receive appointment request.
2. Validate the request.
3. Verify that the patient exists.
4. Verify that the doctor exists.
5. Check slot availability.
6. Create the appointment.
7. Record the operation in the audit log.

## Appointment Modification

Authorized staff can modify appointment details such as:

- Appointment date
- Appointment time
- Appointment type

The updated appointment must pass the same validation and availability checks used during creation.

## Appointment Cancellation

An authorized user can cancel an existing appointment.

The system should:

1. Verify that the appointment exists.
2. Verify user authorization.
3. Change the appointment status to cancelled.
4. Record the cancellation in the audit log.

Cancelled appointments should not be permanently deleted unless the system's data-retention policy explicitly permits deletion.

## Security Requirements

Appointment data must be protected from unauthorized access.

The module must:

- Require authentication.
- Verify authorization.
- Validate appointment input.
- Prevent unauthorized modifications.
- Record important appointment operations.

## API Examples

Create an appointment:

POST /api/appointments

Example request:

{
  "patient_id": "P1001",
  "doctor_id": "D204",
  "date": "2026-10-10",
  "time": "10:30",
  "type": "General Consultation"
}

Retrieve an appointment:

GET /api/appointments/{appointment_id}

Cancel an appointment:

DELETE /api/appointments/{appointment_id}

The cancellation endpoint should perform an authorization check before changing the appointment status.

## Common Developer Questions

### How does an appointment connect to a patient?

The appointment stores the patient's unique patient ID. This allows the system to associate the appointment with the corresponding patient record.

### How does the system prevent double booking?

Before creating or modifying an appointment, the system checks whether the requested doctor and time slot are already occupied.

### Can cancelled appointments be deleted?

The recommended application behavior is to mark appointments as cancelled rather than permanently deleting them, so that the operation remains traceable.

### Which module does Appointment Management depend on?

Appointment Management depends on Patient Management to validate the patient associated with an appointment.
