from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'athlete' or 'coach'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    athlete_profile = db.relationship('AthleteProfile', backref='user', uselist=False)
    coach_profile = db.relationship('CoachProfile', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.email}>'


class AthleteProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(100))
    grad_year = db.Column(db.Integer)
    state = db.Column(db.String(50))
    events = db.Column(db.String(200))  # e.g. "100m,200m,400m"
    bio = db.Column(db.Text)

    personal_bests = db.relationship('PersonalBest', backref='athlete', lazy='dynamic')

    def __repr__(self):
        return f'<Athlete {self.first_name} {self.last_name}>'


class CoachProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    school = db.Column(db.String(100))
    college = db.Column(db.String(100))
    state = db.Column(db.String(50))
    bio = db.Column(db.Text)

    def __repr__(self):
        return f'<Coach {self.first_name} {self.last_name}>'


class PersonalBest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.Integer, db.ForeignKey('athlete_profile.id'), nullable=False)
    event = db.Column(db.String(50), nullable=False)   # e.g. "100m", "400m", "High Jump"
    time_recorded = db.Column(db.String(20), nullable=False)  # e.g. "10.45" or "1:52.30"
    date_achieved = db.Column(db.Date)
    meet_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PR {self.event}: {self.time_recorded}>'