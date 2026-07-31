from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        recipient_id: str,
        message: str,
        related_type: str,
        related_id: str,
    ) -> Notification:
        notification = Notification(
            id=str(uuid4()),
            recipient_id=recipient_id,
            message=message,
            related_type=related_type,
            related_id=related_id,
        )
        self.session.add(notification)
        return notification

    def delete_related(self, *, related_type: str, related_id: str) -> None:
        self.session.execute(
            delete(Notification).where(
                Notification.related_type == related_type,
                Notification.related_id == related_id,
            )
        )
