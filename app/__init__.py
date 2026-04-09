import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.artwork import bp as artwork_bp
    app.register_blueprint(artwork_bp, url_prefix='/artwork')

    from app.social import bp as social_bp
    app.register_blueprint(social_bp, url_prefix='/social')

    from app.channels import bp as channels_bp
    app.register_blueprint(channels_bp, url_prefix='/channels')

    from app.donate import bp as donate_bp
    app.register_blueprint(donate_bp, url_prefix='/donate')

    from app.collections import bp as collections_bp
    app.register_blueprint(collections_bp, url_prefix='/collections')

    from app.dm import bp as dm_bp
    app.register_blueprint(dm_bp, url_prefix='/messages')

    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()
        _run_migrations()

    return app


def _run_migrations():
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    def _add_column_if_missing(table, column, definition):
        try:
            if table not in tables:
                return
            cols = [c['name'] for c in inspector.get_columns(table)]
            if column not in cols:
                with db.engine.connect() as conn:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {definition}'))
                    conn.commit()
        except Exception:
            pass

    _add_column_if_missing('messages', 'image_url', 'VARCHAR(500)')
    _add_column_if_missing('users', 'is_banned', 'BOOLEAN DEFAULT FALSE')
