from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
cache = Cache()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day"])
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)

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

    from app.messages import messages_bp
    app.register_blueprint(messages_bp)

    from app.feedback import feedback_bp
    app.register_blueprint(feedback_bp)

    from app.schools import schools_bp
    app.register_blueprint(schools_bp)

    return app