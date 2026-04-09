from app import db
from app.models import Notification


def create_notification(recipient_id, sender_id, notif_type, artwork_id=None):
    if recipient_id == sender_id:
        return
    n = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        notif_type=notif_type,
        artwork_id=artwork_id,
    )
    db.session.add(n)
