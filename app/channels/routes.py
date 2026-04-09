import time
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from app import db
from app.channels import bp
from app.models import Channel, Message
from app.utils.cloudinary_upload import upload_image


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


@bp.route('/<int:channel_id>/messages')
def messages_json(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    since_id = request.args.get('since', 0, type=int)
    msgs = channel.messages.filter(Message.id > since_id).order_by(Message.created_at.asc()).all()
    return jsonify([{
        'id': m.id,
        'content': m.content,
        'image_src': m.image_src(),
        'author': m.author.username,
        'author_url': f'/profile/{m.author.username}',
        'author_avatar': m.author.profile_image_url(),
        'timestamp': m.created_at.strftime('%H:%M · %b %d')
    } for m in msgs])


@bp.route('/<int:channel_id>', methods=['GET', 'POST'])
def view(channel_id):
    channel = Channel.query.get_or_404(channel_id)
    form = MessageForm()
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please sign in to send messages.', 'error')
            return redirect(url_for('auth.login'))

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
    return render_template('channels/channel.html', title=f'#{channel.name}',
                           channel=channel, messages=messages, form=form, channels=channels)
