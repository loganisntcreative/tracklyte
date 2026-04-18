import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this-later'
    _db_url = os.environ.get('DATABASE_URL') or 'sqlite:///tracklyte.db'
    # Render gives postgres:// but SQLAlchemy needs postgresql://
    SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300