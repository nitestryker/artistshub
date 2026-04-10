import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


def _get_db_url():
    url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
    if not url:
        raise RuntimeError(
            'No database URL configured. Set DATABASE_URL or SUPABASE_DB_URL in your environment.'
        )
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET') or os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'
    SQLALCHEMY_DATABASE_URI = _get_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _db_url = SQLALCHEMY_DATABASE_URI
    _using_pooler = ':6543/' in _db_url or 'pooler.supabase.com' in _db_url

    if _using_pooler:
        from sqlalchemy.pool import NullPool
        SQLALCHEMY_ENGINE_OPTIONS = {
            'poolclass': NullPool,
            'connect_args': {'options': '-c statement_timeout=30000'},
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 280,
            'pool_timeout': 20,
            'pool_size': 5,
            'max_overflow': 2,
        }
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    WTF_CSRF_ENABLED = True
    PORT = int(os.environ.get('PORT', 5000))
