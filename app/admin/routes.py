from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import (User, Artwork, Channel, Message, Collection, Like,
                        Comment, Follower, Report, ChannelBan, ErrorLog, DirectMessage)
from sqlalchemy import func


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


def _get_stats():
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    return {
        'total_users': User.query.count(),
        'total_artworks': Artwork.query.count(),
        'total_albums': Collection.query.count(),
        'total_messages': Message.query.count(),
        'total_donations': 0,
        'new_users_week': User.query.filter(User.created_at >= week_ago).count(),
        'new_artworks_week': Artwork.query.filter(Artwork.created_at >= week_ago).count(),
    }


@bp.route('/')
@login_required
@admin_required
def index():
    return redirect(url_for('admin.users'))


@bp.route('/users')
@login_required
@admin_required
def users():
    stats = _get_stats()
    q = request.args.get('q', '').strip()
    query = User.query
    if q:
        query = query.filter(
            (User.username.ilike(f'%{q}%')) | (User.display_name.ilike(f'%{q}%'))
            if hasattr(User, 'display_name') else User.username.ilike(f'%{q}%')
        )
    all_users = query.order_by(User.created_at.desc()).all()
    user_data = []
    for u in all_users:
        user_data.append({
            'user': u,
            'artwork_count': u.artworks.count(),
        })
    return render_template('admin/users.html', stats=stats, user_data=user_data, q=q)


@bp.route('/users/<int:user_id>/toggle-ban', methods=['POST'])
@login_required
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({'error': 'Cannot ban an admin'}), 400
    user.is_banned = not user.is_banned
    db.session.commit()
    return jsonify({'banned': user.is_banned})


@bp.route('/users/<int:user_id>/set-role', methods=['POST'])
@login_required
@admin_required
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot change your own role'}), 400
    role = request.json.get('role', 'user')
    user.is_admin = (role == 'admin')
    db.session.commit()
    return jsonify({'is_admin': user.is_admin})


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({'error': 'Cannot delete an admin account'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/channels')
@login_required
@admin_required
def channels():
    stats = _get_stats()
    all_channels = Channel.query.order_by(Channel.created_at.desc()).all()
    return render_template('admin/channels.html', stats=stats, channels=all_channels)


@bp.route('/channels/create', methods=['POST'])
@login_required
@admin_required
def create_channel():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Channel name is required.', 'error')
        return redirect(url_for('admin.channels'))
    existing = Channel.query.filter_by(name=name).first()
    if existing:
        flash('A channel with that name already exists.', 'error')
        return redirect(url_for('admin.channels'))
    channel = Channel(name=name, description=description, created_by=current_user.id)
    db.session.add(channel)
    db.session.commit()
    flash(f'Channel #{name} created.', 'success')
    return redirect(url_for('admin.channels'))


@bp.route('/channels/<int:channel_id>')
@login_required
@admin_required
def channel_detail(channel_id):
    stats = _get_stats()
    channel = Channel.query.get_or_404(channel_id)
    tab = request.args.get('tab', 'messages')
    messages = channel.messages.order_by(Message.created_at.desc()).limit(100).all()
    bans = channel.bans.all()
    return render_template('admin/channel_detail.html', stats=stats, channel=channel,
                           tab=tab, messages=messages, bans=bans)


@bp.route('/channels/<int:channel_id>/delete-message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def delete_message(channel_id, message_id):
    msg = Message.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/channels/<int:channel_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_from_channel(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    user_id = request.form.get('user_id', type=int)
    reason = request.form.get('reason', '')
    if not user_id:
        flash('User ID required.', 'error')
        return redirect(url_for('admin.channel_detail', channel_id=channel_id))
    existing = ChannelBan.query.filter_by(channel_id=channel_id, user_id=user_id).first()
    if not existing:
        ban = ChannelBan(channel_id=channel_id, user_id=user_id,
                         banned_by=current_user.id, reason=reason)
        db.session.add(ban)
        db.session.commit()
    flash('User banned from channel.', 'success')
    return redirect(url_for('admin.channel_detail', channel_id=channel_id, tab='bans'))


@bp.route('/channels/<int:channel_id>/unban/<int:ban_id>', methods=['POST'])
@login_required
@admin_required
def unban_from_channel(channel_id, ban_id):
    ban = ChannelBan.query.get_or_404(ban_id)
    db.session.delete(ban)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/channels/<int:channel_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_channel(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    db.session.delete(channel)
    db.session.commit()
    flash(f'Channel #{channel.name} deleted.', 'success')
    return redirect(url_for('admin.channels'))


@bp.route('/reports')
@login_required
@admin_required
def reports():
    stats = _get_stats()
    status_filter = request.args.get('status', 'pending')
    query = Report.query
    if status_filter in ('pending', 'resolved', 'dismissed'):
        query = query.filter_by(status=status_filter)
    all_reports = query.order_by(Report.created_at.desc()).all()
    return render_template('admin/reports.html', stats=stats, reports=all_reports,
                           status_filter=status_filter)


@bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = 'resolved'
    db.session.commit()
    return jsonify({'success': True, 'status': 'resolved'})


@bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = 'dismissed'
    db.session.commit()
    return jsonify({'success': True, 'status': 'dismissed'})


@bp.route('/reports/<int:report_id>/delete-content', methods=['POST'])
@login_required
@admin_required
def delete_content_and_resolve(report_id):
    report = Report.query.get_or_404(report_id)
    if report.artwork_id and report.artwork:
        db.session.delete(report.artwork)
    report.status = 'resolved'
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/artwork/<int:artwork_id>/report', methods=['POST'])
@login_required
def report_artwork(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    reason = request.form.get('reason', 'other')
    notes = request.form.get('notes', '')
    existing = Report.query.filter_by(reporter_id=current_user.id,
                                      artwork_id=artwork_id, status='pending').first()
    if existing:
        flash('You have already reported this artwork.', 'info')
        return redirect(url_for('artwork.detail', artwork_id=artwork_id))
    report = Report(reporter_id=current_user.id, artwork_id=artwork_id,
                    target_type='artwork', reason=reason, notes=notes)
    db.session.add(report)
    db.session.commit()
    flash('Thank you for your report. Our team will review it shortly.', 'success')
    return redirect(url_for('artwork.detail', artwork_id=artwork_id))


@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    stats = _get_stats()
    days = request.args.get('days', 30, type=int)
    if days not in (7, 30, 60, 90):
        days = 30
    now = datetime.utcnow()
    start = now - timedelta(days=days)

    total_likes = Like.query.count()
    total_comments = Comment.query.count()
    total_follows = Follower.query.count()
    total_reports = Report.query.count()
    pending_reports = Report.query.filter_by(status='pending').count()
    total_messages = Message.query.count()
    total_artworks = Artwork.query.count()
    total_users = User.query.count()

    user_growth = _daily_counts(User, User.created_at, start, now)
    artwork_growth = _daily_counts(Artwork, Artwork.created_at, start, now)
    chat_activity = _daily_counts(Message, Message.created_at, start, now)
    report_trend = _daily_counts(Report, Report.created_at, start, now)
    donation_trend = []

    medium_data = db.session.query(Artwork.category, func.count(Artwork.id))\
        .group_by(Artwork.category).all()
    medium_labels = [m[0] for m in medium_data]
    medium_counts = [m[1] for m in medium_data]

    top_artworks = db.session.query(Artwork,
        func.count(Like.id).label('like_count'),
        func.count(Comment.id).label('comment_count'))\
        .outerjoin(Like, Like.artwork_id == Artwork.id)\
        .outerjoin(Comment, Comment.artwork_id == Artwork.id)\
        .group_by(Artwork.id)\
        .order_by(func.count(Like.id).desc())\
        .limit(8).all()

    top_channels = db.session.query(Channel, func.count(Message.id).label('msg_count'))\
        .outerjoin(Message, Message.channel_id == Channel.id)\
        .group_by(Channel.id)\
        .order_by(func.count(Message.id).desc())\
        .limit(10).all()

    top_contributors = db.session.query(User, func.count(Message.id).label('msg_count'))\
        .outerjoin(Message, Message.user_id == User.id)\
        .group_by(User.id)\
        .order_by(func.count(Message.id).desc())\
        .limit(10).all()

    top_followed = db.session.query(User, func.count(Follower.id).label('follower_count'))\
        .outerjoin(Follower, Follower.following_id == User.id)\
        .group_by(User.id)\
        .order_by(func.count(Follower.id).desc())\
        .limit(8).all()

    report_reasons = db.session.query(Report.reason, func.count(Report.id))\
        .group_by(Report.reason).all()
    report_reason_labels = [r[0] for r in report_reasons]
    report_reason_counts = [r[1] for r in report_reasons]

    max_channel_msgs = max((c[1] for c in top_channels), default=1)

    return render_template('admin/analytics.html',
        stats=stats,
        days=days,
        total_likes=total_likes,
        total_comments=total_comments,
        total_follows=total_follows,
        total_reports=total_reports,
        pending_reports=pending_reports,
        total_messages=total_messages,
        total_artworks=total_artworks,
        total_users=total_users,
        user_growth=user_growth,
        artwork_growth=artwork_growth,
        chat_activity=chat_activity,
        report_trend=report_trend,
        donation_trend=donation_trend,
        medium_labels=medium_labels,
        medium_counts=medium_counts,
        top_artworks=top_artworks,
        top_channels=top_channels,
        top_contributors=top_contributors,
        top_followed=top_followed,
        report_reason_labels=report_reason_labels,
        report_reason_counts=report_reason_counts,
        max_channel_msgs=max_channel_msgs,
    )


def _daily_counts(model, date_col, start, end):
    results = db.session.query(
        func.date(date_col).label('day'),
        func.count(model.id).label('cnt')
    ).filter(date_col >= start, date_col <= end)\
     .group_by(func.date(date_col))\
     .order_by(func.date(date_col)).all()
    data = {}
    for row in results:
        data[str(row.day)] = row.cnt
    days = []
    current = start.date()
    while current <= end.date():
        days.append({'date': str(current), 'count': data.get(str(current), 0)})
        current += timedelta(days=1)
    return days


@bp.route('/error-logs')
@login_required
@admin_required
def error_logs():
    stats = _get_stats()
    logs = ErrorLog.query.order_by(ErrorLog.created_at.desc()).limit(200).all()
    return render_template('admin/error_logs.html', stats=stats, logs=logs)


@bp.route('/error-logs/<int:log_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_log(log_id):
    log = ErrorLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/error-logs/clear', methods=['POST'])
@login_required
@admin_required
def clear_logs():
    ErrorLog.query.delete()
    db.session.commit()
    return jsonify({'success': True})
