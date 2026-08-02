import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Booking, BookingSeat, Bus, Payment, Route, Schedule, Ticket, User
from app.routers.deps import get_current_user
from app.schemas import BookingCreateRequest, CancelBookingRequest
from app.services.fare_service import calculate_fare
from app.services.logging_service import log_event
from app.services.ticket_service import build_qr_payload, generate_qr_base64, generate_ticket_number, new_verification_token

router = APIRouter(tags=["booking"])


@router.post("/booking")
def create_booking(payload: BookingCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    schedule = db.get(Schedule, payload.schedule_id)
    if not schedule or schedule.booking_status != "open":
        raise HTTPException(status_code=400, detail="Schedule is not available for booking")
    bus = db.get(Bus, schedule.bus_id)
    route = db.get(Route, schedule.route_id)
    if not bus or not route:
        raise HTTPException(status_code=400, detail="Invalid schedule")

    fare_breakdown = calculate_fare(route, bus, payload.discount)
    total_amount = round(fare_breakdown["final_fare"] * len(payload.seats), 2)
    log_event(db, "price_calculation", f"Calculated amount {total_amount} for schedule {schedule.id}", current_user.id)

    if round(payload.submitted_amount, 2) != total_amount:
        raise HTTPException(status_code=400, detail="Price validation failed. Submitted amount mismatch.")

    if schedule.available_seats < len(payload.seats):
        raise HTTPException(status_code=400, detail="Not enough seats available")

    booking_status = "confirmed" if payload.payment_status == "Success" else "pending"
    booking = Booking(
        user_id=current_user.id,
        schedule_id=schedule.id,
        status=booking_status,
        calculated_fare=total_amount,
        submitted_fare=payload.submitted_amount,
        payment_status=payload.payment_status,
    )
    db.add(booking)
    db.flush()

    for seat in payload.seats:
        db.add(BookingSeat(booking_id=booking.id, schedule_id=schedule.id, seat_number=seat))

    db.add(Payment(booking_id=booking.id, amount=payload.submitted_amount, status=payload.payment_status, transaction_ref=str(uuid.uuid4())))

    ticket_data = None
    if payload.payment_status == "Success":
        schedule.available_seats -= len(payload.seats)
        if schedule.available_seats == 0:
            schedule.booking_status = "full"
        verification_token = new_verification_token()
        ticket_number = generate_ticket_number(booking.id)
        temp_ticket_id = str(uuid.uuid4())
        qr_payload = build_qr_payload(temp_ticket_id, booking.id, verification_token)
        ticket = Ticket(
            id=temp_ticket_id,
            booking_id=booking.id,
            ticket_number=ticket_number,
            verification_token=verification_token,
            qr_payload=qr_payload,
            booking_status="Valid",
        )
        db.add(ticket)
        ticket_data = {
            "ticket_number": ticket.ticket_number,
            "verification_token": ticket.verification_token,
            "qr_code_base64": generate_qr_base64(ticket.qr_payload),
        }

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Selected seat is already booked.") from exc

    log_event(db, "ticket_booking", f"Booking {booking.id} created", current_user.id)
    return {
        "success": True,
        "message": "Booking confirmed" if payload.payment_status == "Success" else "Booking created with non-success payment status",
        "data": {
            "booking_id": booking.id,
            "status": booking.status,
            "fare_breakdown": fare_breakdown,
            "seats": payload.seats,
            "ticket": ticket_data,
        },
    }


@router.post("/cancel-booking")
def cancel_booking(payload: CancelBookingRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    booking = db.get(Booking, payload.booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking already cancelled")
    booking.status = "cancelled"
    schedule = db.get(Schedule, booking.schedule_id)
    seats_count = db.query(BookingSeat).filter(BookingSeat.booking_id == booking.id).count()
    if schedule:
        schedule.available_seats += seats_count
        schedule.booking_status = "open"
    ticket = db.query(Ticket).filter(Ticket.booking_id == booking.id).first()
    if ticket:
        ticket.booking_status = "Cancelled"
    db.commit()
    log_event(db, "ticket_cancellation", f"Booking {booking.id} cancelled", current_user.id)
    return {"success": True, "message": "Booking cancelled"}


@router.get("/bookings/history")
def booking_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    upcoming, previous, cancelled = [], [], []
    for booking in rows:
        schedule = db.get(Schedule, booking.schedule_id)
        item = {
            "booking_id": booking.id,
            "schedule_id": booking.schedule_id,
            "status": booking.status,
            "fare": booking.calculated_fare,
            "payment_status": booking.payment_status,
            "created_at": booking.created_at,
        }
        if booking.status == "cancelled":
            cancelled.append(item)
        elif schedule and schedule.departure_datetime > booking.created_at:
            upcoming.append(item)
        else:
            previous.append(item)
    return {"success": True, "data": {"previous_bookings": previous, "upcoming_trips": upcoming, "cancelled_bookings": cancelled}}


@router.get("/ticket/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    booking = db.get(Booking, ticket.booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to ticket")
    seats = [row.seat_number for row in db.query(BookingSeat).filter(BookingSeat.booking_id == booking.id).all()]
    schedule = db.get(Schedule, booking.schedule_id)
    bus = db.get(Bus, schedule.bus_id) if schedule else None
    route = db.get(Route, schedule.route_id) if schedule else None
    return {
        "success": True,
        "data": {
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "booking_id": booking.id,
            "passenger_name": current_user.full_name,
            "bus_details": bus.operator_name if bus else None,
            "route": f"{route.source_city} -> {route.destination_city}" if route else None,
            "seat_numbers": seats,
            "journey_date": schedule.departure_datetime if schedule else None,
            "booking_date": booking.created_at,
            "qr_code_base64": generate_qr_base64(ticket.qr_payload),
            "booking_status": ticket.booking_status,
            "download_pdf_placeholder": "Use this payload to generate/download PDF in frontend layer.",
        },
    }
