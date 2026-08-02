import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base


class UserRole(str, enum.Enum):
    passenger = "passenger"
    administrator = "administrator"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.passenger, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reset_token: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Bus(Base):
    __tablename__ = "buses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registration_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    operator_name: Mapped[str] = mapped_column(String(120), nullable=False)
    bus_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_layout: Mapped[str] = mapped_column(Text, nullable=False)
    bus_status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    amenities: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Route(Base):
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    destination_city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    intermediate_stops: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    total_distance: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_travel_time: Mapped[str] = mapped_column(String(50), nullable=False)
    base_fare: Mapped[float] = mapped_column(Float, nullable=False)


class Schedule(Base):
    __tablename__ = "schedules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bus_id: Mapped[int] = mapped_column(ForeignKey("buses.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    arrival_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)

    bus = relationship("Bus")
    route = relationship("Route")


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="confirmed", nullable=False, index=True)
    calculated_fare: Mapped[float] = mapped_column(Float, nullable=False)
    submitted_fare: Mapped[float] = mapped_column(Float, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(30), default="Success", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class BookingSeat(Base):
    __tablename__ = "booking_seats"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id"), nullable=False)
    seat_number: Mapped[str] = mapped_column(String(10), nullable=False)

    __table_args__ = (UniqueConstraint("schedule_id", "seat_number", name="uq_schedule_seat"),)


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    verification_token: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    qr_payload: Mapped[str] = mapped_column(Text, nullable=False)
    booking_status: Mapped[str] = mapped_column(String(30), default="Valid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_ref: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class BusPass(Base):
    __tablename__ = "bus_passes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    pass_type: Mapped[str] = mapped_column(String(40), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class ActivityLog(Base):
    __tablename__ = "logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)


Index("ix_route_search", Route.source_city, Route.destination_city)
Index("ix_schedule_search", Schedule.departure_datetime, Schedule.booking_status)
