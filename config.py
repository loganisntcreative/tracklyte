import os
WTF_CSRF_ENABLED = True

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this-later'
    _db_url = os.environ.get('DATABASE_URL') or 'sqlite:///tracklyte.db'
    SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    APP_URL = os.environ.get('APP_URL') or 'http://127.0.0.1:5000'
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = 86400