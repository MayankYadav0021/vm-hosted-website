# Sample Multi-File Codebase

This codebase is created for Week 4 Exercise 6.

## Authentication

Authentication is implemented in:

- auth/auth_service.py
- auth/session.py
- api/auth_routes.py

The `authenticate()` function checks the username and password using
the user service.

## Registration

Registration is implemented through:

- users/registration.py
- users/user_service.py
- api/registration_routes.py

The registration flow validates the input before creating a new user.

## Payments

Payment processing is implemented through:

- payments/payment_service.py
- api/payment_routes.py

The API payment route calls `process_payment()`.

## Tests

The project contains:

- tests/test_auth.py
- tests/test_registration.py
- tests/test_payment.py

These tests cover authentication, registration and payment processing.
