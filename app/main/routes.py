from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Length
from app import db
from app.main import bp
from app.models import User, Artwork, Follower
from app.utils.cloudinary_upload import upload_image
from sqlalchemy import or_ as sql_or

PER_PAGE = 20


class EditProfileForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    profile_image = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    submit = SubmitField('Save Changes')


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        base_q = current_user.feed_artworks()
        pagination = base_q.paginate(page=page, per_page=PER_PAGE, error_out=False)
        if not pagination.items and page == 1:
            pagination = Artwork.query.order_by(Artwork.created_at.desc()).paginate(
                page=page, per_page=PER_PAGE, error_out=False)
    else:
        pagination = Artwork.query.order_by(Artwork.created_at.desc()).paginate(
            page=page, per_page=PER_PAGE, error_out=False)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_template('_partials/masonry_cards.html', artworks=pagination.items)
        return jsonify({'html': html, 'has_next': pagination.has_next,
                        'next_page': pagination.next_num if pagination.has_next else None})
    return render_template('index.html', title='Home', artworks=pagination.items,
                           has_next=pagination.has_next, next_page=pagination.next_num if pagination.has_next else None)


@bp.route('/explore')
def explore():
    from app.models import Like
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    query = Artwork.query
    if category:
        query = query.filter_by(category=category)
    pagination = query.order_by(Artwork.created_at.desc()).paginate(
        page=page, per_page=24, error_out=False)
    categories = Artwork.CATEGORIES

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_template('_partials/masonry_cards.html', artworks=pagination.items)
        return jsonify({'html': html, 'has_next': pagination.has_next,
                        'next_page': pagination.next_num if pagination.has_next else None})

    # Trending: top 6 artworks by like count overall (only on first page)
    trending_artworks = []
    if page == 1:
        trending = (
            db.session.query(Artwork, db.func.count(Like.id).label('like_count'))
            .outerjoin(Like, Like.artwork_id == Artwork.id)
            .group_by(Artwork.id)
            .order_by(db.text('like_count DESC'))
            .limit(6)
            .all()
        )
        trending_artworks = [row[0] for row in trending if row[1] > 0]

    return render_template('explore.html', title='Explore', artworks=pagination.items,
                           categories=categories, active_category=category,
                           trending_artworks=trending_artworks,
                           has_next=pagination.has_next,
                           next_page=pagination.next_num if pagination.has_next else None)


@bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    artwork_results = []
    user_results = []
    if q:
        like = f'%{q}%'
        artwork_results = Artwork.query.filter(
            sql_or(Artwork.title.ilike(like), Artwork.description.ilike(like))
        ).order_by(Artwork.created_at.desc()).limit(30).all()
        user_results = User.query.filter(
            sql_or(User.username.ilike(like), User.bio.ilike(like))
        ).order_by(User.created_at.desc()).limit(20).all()
    return render_template('search.html', title=f'Search: {q}' if q else 'Search',
                           q=q, artwork_results=artwork_results, user_results=user_results)


@bp.route('/profile/<username>')
def profile(username):
    from app.models import Collection
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    artwork_pagination = user.artworks.order_by(Artwork.created_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False)
    collections = user.collections.order_by(Collection.created_at.desc()).all()
    is_following = False
    if current_user.is_authenticated:
        is_following = current_user.is_following(user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_template('_partials/profile_art_cards.html', artworks=artwork_pagination.items)
        return jsonify({'html': html, 'has_next': artwork_pagination.has_next,
                        'next_page': artwork_pagination.next_num if artwork_pagination.has_next else None})

    return render_template('profile/profile.html', title=user.username, user=user,
                           artworks=artwork_pagination.items, collections=collections,
                           is_following=is_following,
                           artwork_total=user.artworks.count(),
                           has_next=artwork_pagination.has_next,
                           next_page=artwork_pagination.next_num if artwork_pagination.has_next else None)


@bp.route('/admin/verify/<int:user_id>', methods=['POST'])
@login_required
def admin_toggle_verified(user_id):
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()
    status = 'verified' if user.is_verified else 'unverified'
    flash(f'{user.username} is now {status}.', 'success')
    return redirect(url_for('main.profile', username=user.username))


@bp.route('/artists')
def artists():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'new')
    query = User.query
    if sort == 'popular':
        query = query.outerjoin(Follower, Follower.following_id == User.id).group_by(User.id).order_by(db.func.count(Follower.id).desc())
    else:
        query = query.order_by(User.created_at.desc())
    users = query.paginate(page=page, per_page=24, error_out=False)
    return render_template('artists.html', title='Browse Artists', users=users, sort=sort)


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.profile_image.data:
            image_url = upload_image(
                form.profile_image.data.stream,
                public_id=f'avatar_{current_user.id}',
                folder='artapp/avatars',
            )
            current_user.profile_image = image_url
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('main.profile', username=current_user.username))
    elif request.method == 'GET':
        form.bio.data = current_user.bio
    return render_template('profile/settings.html', title='Settings', form=form)
