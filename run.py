from app import create_app, db
from app.models import User, Artwork, Follower, Like, Comment, Channel, Message
from config import Config

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Artwork': Artwork,
        'Follower': Follower,
        'Like': Like,
        'Comment': Comment,
        'Channel': Channel,
        'Message': Message
    }


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True)
