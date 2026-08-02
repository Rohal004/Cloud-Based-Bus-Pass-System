from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class MessageResponse(BaseModel):
    success: bool
    message: str


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: str
    password: str = Field(min_length=8)
    role: Literal["passenger", "administrator"] = "passenger"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    token: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None


class BusUpsertRequest(BaseModel):
    registration_number: str
    operator_name: str
    bus_type: str
    total_seats: int = Field(gt=0)
    bus_status: str = "active"
    amenities: list[str] = []


class RouteUpsertRequest(BaseModel):
    source_city: str
    destination_city: str
    intermediate_stops: list[str] = []
    total_distance: float = Field(gt=0)
    estimated_travel_time: str
    base_fare: float = Field(gt=0)


class ScheduleCreateRequest(BaseModel):
    bus_id: int
    route_id: int
    departure_datetime: datetime
    arrival_datetime: datetime


class BookingCreateRequest(BaseModel):
    schedule_id: int
    seats: list[str] = Field(min_length=1)
    submitted_amount: float = Field(gt=0)
    payment_status: Literal["Success", "Failure", "Pending"] = "Success"
    discount: float = 0


class VerifyTicketRequest(BaseModel):
    verification_token: str


class CancelBookingRequest(BaseModel):
    booking_id: str
