from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

EXPECTED_FARE = 341.25


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register_and_login(client: TestClient, email: str, role: str = "passenger") -> str:
    password = "StrongPass123"
    res = client.post(
        "/register",
        json={
            "full_name": "Test User",
            "email": email,
            "phone_number": "9999999999",
            "password": password,
            "role": role,
        },
    )
    assert res.status_code == 200
    login = client.post("/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["access_token"]


def setup_schedule(client: TestClient, admin_token: str):
    headers = {"Authorization": "Bearer " + admin_token}
    bus_res = client.post(
        "/buses",
        headers=headers,
        json={
            "registration_number": "BUS-100",
            "operator_name": "CityLine",
            "bus_type": "ac",
            "total_seats": 10,
            "bus_status": "active",
            "amenities": ["wifi"],
        },
    )
    route_res = client.post(
        "/routes",
        headers=headers,
        json={
            "source_city": "A",
            "destination_city": "B",
            "intermediate_stops": ["C"],
            "total_distance": 100,
            "estimated_travel_time": "2h",
            "base_fare": 200,
        },
    )
    bus_id = bus_res.json()["data"]["bus_id"]
    route_id = route_res.json()["data"]["route_id"]
    schedule = client.post(
        "/schedules",
        headers=headers,
        json={
            "bus_id": bus_id,
            "route_id": route_id,
            "departure_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "arrival_datetime": (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat(),
        },
    )
    return schedule.json()["data"]["schedule_id"]


def test_fare_calculation_and_price_validation(client: TestClient):
    admin = register_and_login(client, "admin@example.com", role="administrator")
    user_token = register_and_login(client, "user@example.com")
    schedule_id = setup_schedule(client, admin)

    ok = client.post(
        "/booking",
        headers={"Authorization": "Bearer " + user_token},
        json={"schedule_id": schedule_id, "seats": ["1A"], "submitted_amount": EXPECTED_FARE, "payment_status": "Success", "discount": 0},
    )
    assert ok.status_code == 200
    mismatch = client.post(
        "/booking",
        headers={"Authorization": "Bearer " + user_token},
        json={"schedule_id": schedule_id, "seats": ["1B"], "submitted_amount": 100.0, "payment_status": "Success", "discount": 0},
    )
    assert mismatch.status_code == 400
    assert "Price validation failed" in mismatch.json()["message"]


def test_duplicate_seat_booking_prevented(client: TestClient):
    admin = register_and_login(client, "admin2@example.com", role="administrator")
    user1 = register_and_login(client, "u1@example.com")
    user2 = register_and_login(client, "u2@example.com")
    schedule_id = setup_schedule(client, admin)

    payload = {"schedule_id": schedule_id, "seats": ["2A"], "submitted_amount": EXPECTED_FARE, "payment_status": "Success", "discount": 0}
    first = client.post("/booking", headers={"Authorization": "Bearer " + user1}, json=payload)
    assert first.status_code == 200
    second = client.post("/booking", headers={"Authorization": "Bearer " + user2}, json=payload)
    assert second.status_code == 409
    assert "already booked" in second.json()["message"]


def test_ticket_verification_cancelled_status(client: TestClient):
    admin = register_and_login(client, "admin3@example.com", role="administrator")
    user_token = register_and_login(client, "u3@example.com")
    schedule_id = setup_schedule(client, admin)

    book = client.post(
        "/booking",
        headers={"Authorization": "Bearer " + user_token},
        json={"schedule_id": schedule_id, "seats": ["3A"], "submitted_amount": EXPECTED_FARE, "payment_status": "Success", "discount": 0},
    )
    booking_id = book.json()["data"]["booking_id"]
    token = book.json()["data"]["ticket"]["verification_token"]

    valid = client.post("/verify-ticket", json={"verification_token": token})
    assert valid.status_code == 200
    assert valid.json()["data"]["status"] == "Valid"

    cancel = client.post("/cancel-booking", headers={"Authorization": "Bearer " + user_token}, json={"booking_id": booking_id})
    assert cancel.status_code == 200

    cancelled = client.post("/verify-ticket", json={"verification_token": token})
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "Cancelled"
