from sqlalchemy.orm import Session

from app.models import ActivityLog


def log_event(db: Session, action: str, details: str, user_id: str | None = None) -> None:
    db.add(ActivityLog(action=action, details=details, user_id=user_id))
    db.commit()
