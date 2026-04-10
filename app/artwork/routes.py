import time
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app import db
from app.artwork import bp
from app.models import Artwork, Like, Comment
from app.utils.cloudinary_upload import upload_image


_CATEGORY_CHOICES = [
    ('digital', 'Digital Art'), ('painting', 'Painting'),
    ('drawing', 'Drawing & Illustration'), ('photography', 'Photography'),
    ('sculpture', 'Sculpture'), ('mixed_media', 'Mixed Media'),
    ('printmaking', 'Printmaking'), ('textile', 'Textile & Fiber'),
    ('ceramics', 'Ceramics'), ('street', 'Street Art'), ('other', 'Other'),
]


class UploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=2000)])
    category = SelectField('Category', choices=_CATEGORY_CHOICES, default='other')
    tags = StringField('Tags', validators=[Optional(), Length(max=500)])
    image = FileField('Artwork Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only.')
    ])
    submit = SubmitField('Upload Artwork')


class EditArtworkForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=2000)])
    category = SelectField('Category', choices=_CATEGORY_CHOICES, default='other')
    tags = StringField('Tags', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Changes')


class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post Comment')


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    suggested_tags = []

    if request.method == 'POST' and 'image' in request.files:
        image_file = request.files['image']
        if image_file and image_file.filename:
            image_bytes = image_file.read()
            image_file.seek(0)

            if not form.tags.data:
                try:
                    from app.utils.tagging import generate_tags
                    suggested_tags = generate_tags(image_bytes=image_bytes)
                except Exception:
                    suggested_tags = []

    if form.validate_on_submit():
        f = form.image.data
        public_id = f'art_{current_user.id}_{int(time.time())}'
        image_url = upload_image(f.stream, public_id=public_id, folder='artapp/artwork')

        raw_tags = form.tags.data or ''
        tag_list = [t.strip() for t in raw_tags.split(',') if t.strip()]

        artwork = Artwork(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            image_url=image_url,
            user_id=current_user.id,
            tags=', '.join(tag_list),
        )
        db.session.add(artwork)
        db.session.commit()
        flash('Artwork uploaded!', 'success')
        return redirect(url_for('artwork.detail', artwork_id=artwork.id))

    return render_template('artwork/upload.html', title='Upload Artwork',
                           form=form, suggested_tags=suggested_tags)


@bp.route('/preview-tags', methods=['POST'])
@login_required
def preview_tags():
    if 'image' not in request.files:
        return jsonify({'tags': []})
    image_file = request.files['image']
    if not image_file or not image_file.filename:
        return jsonify({'tags': []})
    try:
        from app.utils.tagging import generate_tags
        image_bytes = image_file.read()
        tags = generate_tags(image_bytes=image_bytes)
        return jsonify({'tags': tags})
    except Exception as e:
        return jsonify({'tags': [], 'error': str(e)})


@bp.route('/<int:artwork_id>')
def detail(artwork_id):
    from app.models import Collection, CollectionArtwork
    artwork = Artwork.query.get_or_404(artwork_id)
    form = CommentForm()
    comments = artwork.comments.order_by(Comment.created_at.asc()).all()
    user_collections = []
    artwork_collection_ids = set()
    if current_user.is_authenticated:
        user_collections = current_user.collections.order_by(Collection.created_at.desc()).all()
        artwork_collection_ids = {
            ca.collection_id for ca in
            CollectionArtwork.query.filter_by(artwork_id=artwork_id).all()
        }
    return render_template('artwork/detail.html', title=artwork.title,
                           artwork=artwork, form=form, comments=comments,
                           user_collections=user_collections,
                           artwork_collection_ids=artwork_collection_ids)


@bp.route('/<int:artwork_id>/comment', methods=['POST'])
@login_required
def add_comment(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            artwork_id=artwork.id
        )
        db.session.add(comment)
        from app.notifications.helpers import create_notification
        create_notification(artwork.user_id, current_user.id, 'comment', artwork_id=artwork.id)
        db.session.commit()
        flash('Comment posted!', 'success')
    return redirect(url_for('artwork.detail', artwork_id=artwork_id))


@bp.route('/<int:artwork_id>/like', methods=['POST'])
@login_required
def toggle_like(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    existing = Like.query.filter_by(user_id=current_user.id, artwork_id=artwork_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        like = Like(user_id=current_user.id, artwork_id=artwork_id)
        db.session.add(like)
        liked = True
        from app.notifications.helpers import create_notification
        create_notification(artwork.user_id, current_user.id, 'like', artwork_id=artwork_id)
    db.session.commit()
    return jsonify({'liked': liked, 'count': artwork.like_count()})


@bp.route('/<int:artwork_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_artwork(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.user_id != current_user.id:
        flash('Not authorized.', 'error')
        return redirect(url_for('artwork.detail', artwork_id=artwork_id))
    form = EditArtworkForm()
    if form.validate_on_submit():
        artwork.title = form.title.data
        artwork.description = form.description.data
        artwork.category = form.category.data
        raw_tags = form.tags.data or ''
        tag_list = [t.strip() for t in raw_tags.split(',') if t.strip()]
        artwork.tags = ', '.join(tag_list)
        db.session.commit()
        flash('Artwork updated!', 'success')
        return redirect(url_for('artwork.detail', artwork_id=artwork_id))
    elif request.method == 'GET':
        form.title.data = artwork.title
        form.description.data = artwork.description
        form.category.data = artwork.category
        form.tags.data = artwork.tags or ''
    return render_template('artwork/edit.html', title='Edit Artwork', form=form, artwork=artwork)


@bp.route('/<int:artwork_id>/delete', methods=['POST'])
@login_required
def delete_artwork(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.user_id != current_user.id and not current_user.is_admin:
        flash('Not authorized.', 'error')
        return redirect(url_for('main.index'))
    db.session.delete(artwork)
    db.session.commit()
    flash('Artwork deleted.', 'success')
    return redirect(url_for('main.profile', username=current_user.username))
