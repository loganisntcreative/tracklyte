from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
cache = Cache()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)

    with app.app_context():
        from app import models
        db.create_all()

    from app.routes import main
    app.register_blueprint(main)

    from app.auth import auth
    app.register_blueprint(auth)

    from app.profile import profile_bp
    app.register_blueprint(profile_bp)

    from app.prs import prs_bp
    app.register_blueprint(prs_bp)

    from app.coach import coach_bp
    app.register_blueprint(coach_bp)

    from app.discover import discover_bp
    app.register_blueprint(discover_bp)

    return app