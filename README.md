# Cloud-Based-Bus-Pass-System

Development-phase local implementation of a cloud-ready bus pass and online ticket booking backend.

## Features implemented
- JWT-based authentication with registration, login/logout, forgot/reset password, email verification simulation, and profile APIs.
- Role-based admin endpoints for managing buses, routes, schedules, and viewing users/bookings.
- Bus search and schedule filtering.
- Seat booking workflow with backend fare calculation, price validation, payment mock states, and duplicate-seat protection.
- Digital ticket generation with unique booking/ticket/verification tokens and QR payload generation.
- Ticket verification endpoint for valid/expired/cancelled/already-used checks.
- Activity logging for auth, booking, cancellation, pricing, and verification events.
- Modular architecture (`models`, `routers`, `services`, `core`) with normalized relational schema and indexes.

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run tests
```bash
pytest -q
```
