from flask import jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.notifications import bp
from app.models import Notification


@bp.route('/count')
@login_required
def count():
    n = current_user.notifications.filter_by(read=False).count()
    return jsonify({'count': n})


@bp.route('/list')
@login_required
def list_notifications():
    notifs = (current_user.notifications
              .order_by(Notification.created_at.desc())
              .limit(20).all())
    return jsonify([{
        'id': n.id,
        'type': n.notif_type,
        'text': n.text(),
        'url': n.url(),
        'sender': n.sender.username,
        'sender_avatar': n.sender.profile_image_url(),
        'read': n.read,
        'created_at': n.created_at.strftime('%b %d · %H:%M'),
    } for n in notifs])


@bp.route('/mark-read', methods=['POST'])
@login_required
def mark_all_read():
    current_user.notifications.filter_by(read=False).update({'read': True})
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_one_read(notif_id):
    n = Notification.query.get_or_404(notif_id)
    if n.recipient_id == current_user.id:
        n.read = True
        db.session.commit()
    return jsonify({'ok': True, 'url': n.url()})
