from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Booking, User
from app.routers.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: object = Depends(require_admin)):
    users = db.query(User).all()
    return {
        "success": True,
        "data": [
            {
                "user_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "phone_number": u.phone_number,
                "role": u.role,
                "is_verified": u.is_verified,
                "registration_date": u.registration_date,
            }
            for u in users
        ],
    }


@router.get("/bookings")
def list_bookings(db: Session = Depends(get_db), _: object = Depends(require_admin)):
    bookings = db.query(Booking).all()
    return {
        "success": True,
        "data": [
            {
                "booking_id": b.id,
                "user_id": b.user_id,
                "schedule_id": b.schedule_id,
                "status": b.status,
                "fare": b.calculated_fare,
                "payment_status": b.payment_status,
                "created_at": b.created_at,
            }
            for b in bookings
        ],
    }
