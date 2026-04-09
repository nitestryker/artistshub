from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from sqlalchemy import or_, and_
from app import db
from app.dm import bp
from app.models import DirectMessage, User


class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField('Send')


@bp.route('/')
@login_required
def inbox():
    # Get all users the current user has had a conversation with
    sent = db.session.query(DirectMessage.recipient_id).filter_by(sender_id=current_user.id)
    received = db.session.query(DirectMessage.sender_id).filter_by(recipient_id=current_user.id)
    partner_ids = set([r[0] for r in sent.all()] + [r[0] for r in received.all()])
    partners = User.query.filter(User.id.in_(partner_ids)).all() if partner_ids else []

    # Get last message and unread count per partner
    conversations = []
    for partner in partners:
        last_msg = DirectMessage.query.filter(
            or_(
                and_(DirectMessage.sender_id == current_user.id, DirectMessage.recipient_id == partner.id),
                and_(DirectMessage.sender_id == partner.id, DirectMessage.recipient_id == current_user.id)
            )
        ).order_by(DirectMessage.created_at.desc()).first()
        unread = DirectMessage.query.filter_by(
            sender_id=partner.id, recipient_id=current_user.id, read=False).count()
        conversations.append({'partner': partner, 'last_msg': last_msg, 'unread': unread})

    conversations.sort(key=lambda x: x['last_msg'].created_at if x['last_msg'] else 0, reverse=True)
    return render_template('dm/inbox.html', title='Messages', conversations=conversations)


@bp.route('/with/<username>', methods=['GET', 'POST'])
@login_required
def conversation(username):
    partner = User.query.filter_by(username=username).first_or_404()
    if partner.id == current_user.id:
        return redirect(url_for('dm.inbox'))

    form = MessageForm()
    if form.validate_on_submit():
        msg = DirectMessage(
            sender_id=current_user.id,
            recipient_id=partner.id,
            content=form.content.data
        )
        db.session.add(msg)
        from app.notifications.helpers import create_notification
        create_notification(partner.id, current_user.id, 'message')
        db.session.commit()
        return redirect(url_for('dm.conversation', username=username))

    # Mark messages from partner as read
    DirectMessage.query.filter_by(
        sender_id=partner.id, recipient_id=current_user.id, read=False
    ).update({'read': True})
    db.session.commit()

    messages = DirectMessage.query.filter(
        or_(
            and_(DirectMessage.sender_id == current_user.id, DirectMessage.recipient_id == partner.id),
            and_(DirectMessage.sender_id == partner.id, DirectMessage.recipient_id == current_user.id)
        )
    ).order_by(DirectMessage.created_at.asc()).all()

    return render_template('dm/conversation.html', title=f'Chat with {partner.username}',
                           partner=partner, messages=messages, form=form)


@bp.route('/unread-count')
@login_required
def unread_count():
    count = DirectMessage.query.filter_by(recipient_id=current_user.id, read=False).count()
    return jsonify({'count': count})
