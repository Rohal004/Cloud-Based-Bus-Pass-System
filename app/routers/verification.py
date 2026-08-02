from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Booking, Schedule, Ticket
from app.schemas import VerifyTicketRequest
from app.services.logging_service import log_event

router = APIRouter(tags=["ticket-verification"])


@router.post("/verify-ticket")
def verify_ticket(payload: VerifyTicketRequest, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.verification_token == payload.verification_token).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid ticket")
    booking = db.get(Booking, ticket.booking_id)
    schedule = db.get(Schedule, booking.schedule_id) if booking else None

    status = ticket.booking_status
    if ticket.booking_status == "Cancelled":
        status = "Cancelled"
    elif schedule and schedule.departure_datetime < datetime.utcnow():
        status = "Expired"
    elif ticket.used_at is not None:
        status = "Already Used"
    else:
        status = "Valid"

    log_event(db, "ticket_verification", f"Ticket {ticket.id} checked: {status}", booking.user_id if booking else None)
    return {"success": True, "message": "Ticket verified", "data": {"ticket_id": ticket.id, "status": status}}
