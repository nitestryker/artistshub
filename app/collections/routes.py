from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from app import db
from app.collections import bp
from app.models import Collection, CollectionArtwork, Artwork


class CollectionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    submit = SubmitField('Save Collection')


@bp.route('/')
@login_required
def index():
    collections = current_user.collections.order_by(Collection.created_at.desc()).all()
    return render_template('collections/index.html', title='My Collections', collections=collections)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CollectionForm()
    if form.validate_on_submit():
        col = Collection(name=form.name.data, description=form.description.data,
                         user_id=current_user.id)
        db.session.add(col)
        db.session.commit()
        flash(f'Collection "{col.name}" created!', 'success')
        return redirect(url_for('collections.view', collection_id=col.id))
    return render_template('collections/create.html', title='New Collection', form=form)


@bp.route('/<int:collection_id>')
def view(collection_id):
    col = Collection.query.get_or_404(collection_id)
    artworks = [item.artwork for item in col.items.all()]
    return render_template('collections/view.html', title=col.name, collection=col, artworks=artworks)


@bp.route('/<int:collection_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(collection_id):
    col = Collection.query.get_or_404(collection_id)
    if col.user_id != current_user.id:
        flash('Not authorized.', 'error')
        return redirect(url_for('collections.view', collection_id=collection_id))
    form = CollectionForm()
    if form.validate_on_submit():
        col.name = form.name.data
        col.description = form.description.data
        db.session.commit()
        flash('Collection updated!', 'success')
        return redirect(url_for('collections.view', collection_id=col.id))
    elif request.method == 'GET':
        form.name.data = col.name
        form.description.data = col.description
    return render_template('collections/create.html', title='Edit Collection', form=form, collection=col)


@bp.route('/<int:collection_id>/delete', methods=['POST'])
@login_required
def delete(collection_id):
    col = Collection.query.get_or_404(collection_id)
    if col.user_id != current_user.id:
        flash('Not authorized.', 'error')
        return redirect(url_for('main.index'))
    db.session.delete(col)
    db.session.commit()
    flash('Collection deleted.', 'success')
    return redirect(url_for('collections.index'))


@bp.route('/add-artwork', methods=['POST'])
@login_required
def add_artwork():
    artwork_id = request.json.get('artwork_id')
    collection_id = request.json.get('collection_id')
    col = Collection.query.get_or_404(collection_id)
    if col.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    existing = CollectionArtwork.query.filter_by(
        collection_id=collection_id, artwork_id=artwork_id).first()
    if not existing:
        pos = col.items.count()
        ca = CollectionArtwork(collection_id=collection_id, artwork_id=artwork_id, position=pos)
        db.session.add(ca)
        db.session.commit()
        return jsonify({'added': True, 'count': col.artwork_count()})
    return jsonify({'added': False, 'count': col.artwork_count()})


@bp.route('/<int:collection_id>/remove/<int:artwork_id>', methods=['POST'])
@login_required
def remove_artwork(collection_id, artwork_id):
    col = Collection.query.get_or_404(collection_id)
    if col.user_id != current_user.id:
        flash('Not authorized.', 'error')
        return redirect(url_for('collections.view', collection_id=collection_id))
    ca = CollectionArtwork.query.filter_by(collection_id=collection_id, artwork_id=artwork_id).first()
    if ca:
        db.session.delete(ca)
        db.session.commit()
        flash('Removed from collection.', 'success')
    return redirect(url_for('collections.view', collection_id=collection_id))
