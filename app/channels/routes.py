import time
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app import db
from app.channels import bp
from app.models import Channel, Message, User, ChannelBan, PinnedMessage, MessageReport, Report, Notification
from app.utils.cloudinary_upload import upload_image

# In-memory kick registry: {(channel_id, user_id): (reason, expires_at)}
# Kicked users are detected on their next poll and the record expires after 60 seconds.
_kicked = {}
_KICK_TTL = 60  # seconds


def _record_kick(channel_id, user_id, reason):
    _kicked[(channel_id, user_id)] = (reason, time.time() + _KICK_TTL)


def _check_and_consume_kick(channel_id, user_id):
    key = (channel_id, user_id)
    entry = _kicked.get(key)
    if not entry:
        return None
    reason, expires_at = entry
    del _kicked[key]
    if time.time() > expires_at:
        return None
    return reason


class ChannelForm(FlaskForm):
    name = StringField('Channel Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create Channel')


class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[Optional(), Length(max=2000)])
    image = FileField('Attach Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only.')
    ])
    submit = SubmitField('Send')


@bp.route('/')
def index():
    channels = Channel.query.order_by(Channel.created_at.desc()).all()
    return render_template('channels/index.html', title='Channels', channels=channels)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin:
        flash('Only admins can create channels.', 'error')
        return redirect(url_for('channels.index'))
    form = ChannelForm()
    if form.validate_on_submit():
        existing = Channel.query.filter_by(name=form.name.data).first()
        if existing:
            flash('A channel with that name already exists.', 'error')
            return render_template('channels/create.html', form=form)
        channel = Channel(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )
        db.session.add(channel)
        db.session.commit()
        flash(f'Channel #{channel.name} created!', 'success')
        return redirect(url_for('channels.view', channel_id=channel.id))
    return render_template('channels/create.html', title='Create Channel', form=form)


def _msg_dict(m, pinned_ids=None, current_user_id=None, is_privileged=False):
    is_pinned = pinned_ids is not None and m.id in pinned_ids
    return {
        'id': m.id,
        'content': m.content or '',
        'image_src': m.image_src(),
        'author': m.author.username,
        'author_id': m.author.id,
        'author_url': f'/profile/{m.author.username}',
        'author_avatar': m.author.profile_image_url(),
        'author_is_admin': m.author.is_admin,
        'author_is_mod': m.author.is_moderator,
        'author_is_donor': m.author.is_donor,
        'timestamp': m.created_at.strftime('%H:%M · %b %d'),
        'is_pinned': is_pinned,
        'is_own': current_user_id == m.author.id,
        'is_privileged': is_privileged,
    }


@bp.route('/<int:channel_id>/messages')
def messages_json(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    since_id = request.args.get('since', 0, type=int)
    msgs = channel.messages.filter(Message.id > since_id).order_by(Message.created_at.asc()).all()
    pinned_ids = {p.message_id for p in channel.pinned_messages.all()}
    current_id = current_user.id if current_user.is_authenticated else None
    is_priv = current_user.is_authenticated and current_user.is_privileged()

    response = {'messages': [_msg_dict(m, pinned_ids, current_id, is_priv) for m in msgs]}

    if current_user.is_authenticated:
        kick_reason = _check_and_consume_kick(channel_id, current_user.id)
        if kick_reason is not None:
            response['kicked'] = True
            response['kick_reason'] = kick_reason

    return jsonify(response)


@bp.route('/<int:channel_id>', methods=['GET', 'POST'])
def view(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    form = MessageForm()

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please sign in to send messages.', 'error')
            return redirect(url_for('auth.login'))

        ban = ChannelBan.query.filter_by(channel_id=channel_id, user_id=current_user.id).first()
        if ban:
            flash('You are banned from this channel.', 'error')
            return redirect(url_for('channels.view', channel_id=channel_id))

        content = request.form.get('content', '').strip()
        image_file = request.files.get('image')
        image_filename = None

        if image_file and image_file.filename:
            allowed = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
            ext = image_file.filename.rsplit('.', 1)
            if len(ext) == 2 and ext[1].lower() in allowed:
                public_id = f'msg_{current_user.id}_{int(time.time())}'
                image_filename = upload_image(image_file.stream, public_id=public_id, folder='artapp/messages')

        if not content and not image_filename:
            flash('Message cannot be empty.', 'error')
            return redirect(url_for('channels.view', channel_id=channel_id))

        msg = Message(
            content=content,
            image_url=image_filename,
            user_id=current_user.id,
            channel_id=channel.id
        )
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for('channels.view', channel_id=channel_id))

    messages = channel.messages.order_by(Message.created_at.asc()).all()
    channels = Channel.query.order_by(Channel.created_at.desc()).all()
    pinned_ids = {p.message_id for p in channel.pinned_messages.all()}
    pinned_messages = channel.pinned_messages.order_by(PinnedMessage.pinned_at.desc()).all()
    is_banned = False
    if current_user.is_authenticated:
        is_banned = ChannelBan.query.filter_by(
            channel_id=channel_id, user_id=current_user.id).first() is not None

    return render_template('channels/channel.html', title=f'#{channel.name}',
                           channel=channel, messages=messages, form=form, channels=channels,
                           pinned_ids=pinned_ids, pinned_messages=pinned_messages,
                           is_banned=is_banned)


@bp.route('/<int:channel_id>/pin/<int:message_id>', methods=['POST'])
@login_required
def pin_message(channel_id, message_id):
    if not current_user.is_privileged():
        return jsonify({'error': 'Permission denied'}), 403
    existing = PinnedMessage.query.filter_by(channel_id=channel_id, message_id=message_id).first()
    if existing:
        return jsonify({'error': 'Already pinned'}), 400
    pin = PinnedMessage(channel_id=channel_id, message_id=message_id, pinned_by=current_user.id)
    db.session.add(pin)
    db.session.commit()
    msg = Message.query.get(message_id)
    return jsonify({
        'success': True,
        'system_message': {
            'type': 'pin',
            'text': f'📌 {current_user.username} pinned a message.',
        },
        'pin_count': PinnedMessage.query.filter_by(channel_id=channel_id).count(),
        'pinned_msg': _msg_dict(msg) if msg else None,
    })


@bp.route('/<int:channel_id>/unpin/<int:message_id>', methods=['POST'])
@login_required
def unpin_message(channel_id, message_id):
    if not current_user.is_privileged():
        return jsonify({'error': 'Permission denied'}), 403
    pin = PinnedMessage.query.filter_by(channel_id=channel_id, message_id=message_id).first()
    if not pin:
        return jsonify({'error': 'Not pinned'}), 400
    db.session.delete(pin)
    db.session.commit()
    return jsonify({
        'success': True,
        'system_message': {
            'type': 'unpin',
            'text': f'📌 {current_user.username} unpinned a message.',
        },
        'pin_count': PinnedMessage.query.filter_by(channel_id=channel_id).count(),
    })


@bp.route('/<int:channel_id>/delete-message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(channel_id, message_id):
    if not current_user.is_privileged():
        return jsonify({'error': 'Permission denied'}), 403
    msg = Message.query.get(message_id)
    if not msg:
        return jsonify({'error': 'Message not found'}), 404
    Report.query.filter_by(message_id=message_id).update({'message_id': None})
    PinnedMessage.query.filter_by(message_id=message_id).delete()
    db.session.delete(msg)
    db.session.commit()
    return jsonify({
        'success': True,
        'system_message': {
            'type': 'delete',
            'text': f'🗑 A message was deleted by {current_user.username}.',
        },
        'pin_count': PinnedMessage.query.filter_by(channel_id=channel_id).count(),
    })


@bp.route('/<int:channel_id>/kick', methods=['POST'])
@login_required
def kick_user(channel_id):
    if not current_user.is_privileged():
        return jsonify({'error': 'Permission denied', 'system_message': {
            'type': 'error', 'text': '⚠ You do not have permission to use /kick.'
        }}), 403
    data = request.get_json()
    username = data.get('username', '').strip()
    reason = data.get('reason', '').strip()
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({'error': f'User @{username} not found.', 'system_message': {
            'type': 'error', 'text': f'⚠ User @{username} not found.'
        }}), 404
    _record_kick(channel_id, target.id, reason)
    return jsonify({
        'success': True,
        'system_message': {
            'type': 'kick',
            'text': f'🛡 {target.username} was kicked{" — " + reason if reason else ""}.',
        }
    })


@bp.route('/<int:channel_id>/ban-user', methods=['POST'])
@login_required
def ban_user(channel_id):
    if not current_user.is_privileged():
        return jsonify({'error': 'Permission denied', 'system_message': {
            'type': 'error', 'text': '⚠ You do not have permission to use /ban.'
        }}), 403
    data = request.get_json()
    username = data.get('username', '').strip()
    reason = data.get('reason', '').strip()
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({'error': f'User @{username} not found.', 'system_message': {
            'type': 'error', 'text': f'⚠ User @{username} not found.'
        }}), 404
    existing = ChannelBan.query.filter_by(channel_id=channel_id, user_id=target.id).first()
    if not existing:
        ban = ChannelBan(channel_id=channel_id, user_id=target.id,
                         banned_by=current_user.id, reason=reason)
        db.session.add(ban)
        db.session.commit()
    return jsonify({
        'success': True,
        'system_message': {
            'type': 'ban',
            'text': f'🛡 {target.username} was banned from this channel{" — " + reason if reason else ""}.',
        }
    })


@bp.route('/<int:channel_id>/unban-user', methods=['POST'])
@login_required
def unban_user(channel_id):
    if not current_user.is_privileged():
        return jsonify({'error': 'Permission denied', 'system_message': {
            'type': 'error', 'text': '⚠ You do not have permission to use /unban.'
        }}), 403
    data = request.get_json()
    username = data.get('username', '').strip()
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({'error': f'User @{username} not found.', 'system_message': {
            'type': 'error', 'text': f'⚠ User @{username} not found.'
        }}), 404
    ban = ChannelBan.query.filter_by(channel_id=channel_id, user_id=target.id).first()
    if ban:
        db.session.delete(ban)
        db.session.commit()
    return jsonify({
        'success': True,
        'system_message': {
            'type': 'unban',
            'text': f'🛡 {target.username} has been unbanned from this channel.',
        }
    })


@bp.route('/<int:channel_id>/report-message/<int:message_id>', methods=['POST'])
@login_required
def report_message(channel_id, message_id):
    data = request.get_json()
    reason = data.get('reason', 'other')
    notes = data.get('notes', '')
    msg = Message.query.get_or_404(message_id)
    if msg.user_id == current_user.id:
        return jsonify({'error': 'Cannot report your own message'}), 400
    existing = Report.query.filter_by(
        reporter_id=current_user.id, message_id=message_id, status='pending').first()
    if existing:
        return jsonify({'error': 'Already reported'}), 400
    report = Report(
        reporter_id=current_user.id,
        message_id=message_id,
        channel_id=channel_id,
        target_type='message',
        reason=reason,
        notes=notes,
    )
    db.session.add(report)
    admins = User.query.filter_by(is_admin=True).all()
    for admin in admins:
        if admin.id != current_user.id:
            notif = Notification(
                recipient_id=admin.id,
                sender_id=current_user.id,
                notif_type='report',
            )
            db.session.add(notif)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/mention-search')
@login_required
def mention_search():
    q = request.args.get('q', '').strip()
    channel_id = request.args.get('channel_id', type=int)
    if not q and channel_id:
        recent_user_ids = db.session.query(Message.user_id).filter_by(
            channel_id=channel_id).distinct().limit(20).all()
        ids = [r[0] for r in recent_user_ids]
        users = User.query.filter(User.id.in_(ids)).limit(10).all() if ids else []
    else:
        users = User.query.filter(User.username.ilike(f'%{q}%')).limit(10).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'avatar': u.profile_image_url(),
    } for u in users])


@bp.route('/<int:channel_id>/check-ban')
@login_required
def check_ban(channel_id):
    ban = ChannelBan.query.filter_by(channel_id=channel_id, user_id=current_user.id).first()
    return jsonify({'is_banned': ban is not None})
