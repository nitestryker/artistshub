from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    bio = db.Column(db.Text, default='')
    profile_image = db.Column(db.String(256), default='')
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    artworks = db.relationship('Artwork', backref='artist', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    following = db.relationship(
        'Follower',
        foreign_keys='Follower.follower_id',
        backref=db.backref('follower_user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    followers = db.relationship(
        'Follower',
        foreign_keys='Follower.following_id',
        backref=db.backref('following_user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_following(self, user):
        return self.following.filter_by(following_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            f = Follower(follower_id=self.id, following_id=user.id)
            db.session.add(f)

    def unfollow(self, user):
        f = self.following.filter_by(following_id=user.id).first()
        if f:
            db.session.delete(f)

    def follower_count(self):
        return self.followers.count()

    def following_count(self):
        return self.following.count()

    def feed_artworks(self):
        followed_ids = [f.following_id for f in self.following.all()]
        followed_ids.append(self.id)
        return Artwork.query.filter(Artwork.user_id.in_(followed_ids)).order_by(Artwork.created_at.desc())

    def profile_image_url(self):
        if self.profile_image:
            return f'/static/uploads/{self.profile_image}'
        return f'https://ui-avatars.com/api/?name={self.username}&background=6d28d9&color=fff&size=200'

    def __repr__(self):
        return f'<User {self.username}>'


class Artwork(db.Model):
    __tablename__ = 'artworks'

    CATEGORIES = [
        ('digital', 'Digital Art'),
        ('painting', 'Painting'),
        ('drawing', 'Drawing & Illustration'),
        ('photography', 'Photography'),
        ('sculpture', 'Sculpture'),
        ('mixed_media', 'Mixed Media'),
        ('printmaking', 'Printmaking'),
        ('textile', 'Textile & Fiber'),
        ('ceramics', 'Ceramics'),
        ('street', 'Street Art'),
        ('other', 'Other'),
    ]

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    category = db.Column(db.String(50), default='other', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    comments = db.relationship('Comment', backref='artwork', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='artwork', lazy='dynamic', cascade='all, delete-orphan')

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()

    def is_liked_by(self, user):
        if user is None or not user.is_authenticated:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    def image_src(self):
        if self.image_url.startswith('http'):
            return self.image_url
        return f'/static/uploads/{self.image_url}'

    def __repr__(self):
        return f'<Artwork {self.title}>'


class Follower(db.Model):
    __tablename__ = 'followers'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id'),)


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'artwork_id'),)


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Channel(db.Model):
    __tablename__ = 'channels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('Message', backref='channel', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])

    def message_count(self):
        return self.messages.count()


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id'), nullable=False)
    content = db.Column(db.Text, default='')
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def image_src(self):
        if not self.image_url:
            return None
        if self.image_url.startswith('http'):
            return self.image_url
        return f'/static/uploads/{self.image_url}'


class Collection(db.Model):
    __tablename__ = 'collections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref=db.backref('collections', lazy='dynamic'))
    items = db.relationship('CollectionArtwork', backref='collection',
                            lazy='dynamic', cascade='all, delete-orphan',
                            order_by='CollectionArtwork.position')

    def artwork_count(self):
        return self.items.count()

    def cover_image(self):
        first = self.items.first()
        return first.artwork.image_src() if first else None


class CollectionArtwork(db.Model):
    __tablename__ = 'collection_artworks'

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=False)
    position = db.Column(db.Integer, default=0)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    artwork = db.relationship('Artwork', backref=db.backref('collection_items', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('collection_id', 'artwork_id'),)


class Notification(db.Model):
    __tablename__ = 'notifications'

    TYPES = {
        'follow': 'started following you',
        'like': 'liked your artwork',
        'comment': 'commented on your artwork',
        'message': 'sent you a message',
    }

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notif_type = db.Column(db.String(20), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artworks.id'), nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    recipient = db.relationship('User', foreign_keys=[recipient_id],
                                backref=db.backref('notifications', lazy='dynamic'))
    sender = db.relationship('User', foreign_keys=[sender_id])
    artwork = db.relationship('Artwork', foreign_keys=[artwork_id])

    def text(self):
        return self.TYPES.get(self.notif_type, '')

    def url(self):
        if self.notif_type in ('like', 'comment') and self.artwork_id:
            return f'/artwork/{self.artwork_id}'
        if self.notif_type == 'follow':
            return f'/profile/{self.sender.username}'
        if self.notif_type == 'message':
            return f'/messages/with/{self.sender.username}'
        return '/'


class DirectMessage(db.Model):
    __tablename__ = 'direct_messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    sender = db.relationship('User', foreign_keys=[sender_id],
                             backref=db.backref('sent_messages', lazy='dynamic'))
    recipient = db.relationship('User', foreign_keys=[recipient_id],
                                backref=db.backref('received_messages', lazy='dynamic'))
