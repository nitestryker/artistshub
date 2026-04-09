from flask import redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.social import bp
from app.models import User


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash("You can't follow yourself.", 'error')
        return redirect(url_for('main.profile', username=username))
    current_user.follow(user)
    db.session.commit()
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'following': True,
            'followers': user.follower_count()
        })
    flash(f'You are now following {username}.', 'success')
    return redirect(url_for('main.profile', username=username))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        return redirect(url_for('main.profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'following': False,
            'followers': user.follower_count()
        })
    flash(f'You unfollowed {username}.', 'info')
    return redirect(url_for('main.profile', username=username))
