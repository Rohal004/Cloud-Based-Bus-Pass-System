import base64
import json
from datetime import datetime
from io import BytesIO

import qrcode

from app.core.security import random_token


def generate_ticket_number(booking_id: str) -> str:
    return f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{booking_id[:8]}"


def build_qr_payload(ticket_id: str, booking_id: str, verification_token: str) -> str:
    return json.dumps({"ticket_id": ticket_id, "booking_id": booking_id, "verification_token": verification_token})


def generate_qr_base64(payload: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def new_verification_token() -> str:
    return random_token(24)
