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


def run_migrations():
    from sqlalchemy import text, inspect
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('messages')]
        if 'image_url' not in cols:
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE messages ADD COLUMN image_url VARCHAR(500)'))
                conn.commit()
        if 'content' in cols:
            try:
                with db.engine.connect() as conn:
                    db_type = db.engine.dialect.name
                    if db_type == 'sqlite':
                        pass
                    else:
                        conn.execute(text('ALTER TABLE messages ALTER COLUMN content DROP NOT NULL'))
                        conn.commit()
            except Exception:
                pass


if __name__ == '__main__':
    run_migrations()
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True)
