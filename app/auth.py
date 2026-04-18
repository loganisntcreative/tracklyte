from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models import User
from app.email import send_verification_email
import secrets

auth = Blueprint('auth', __name__)


def verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_verified:
            flash('Please verify your email first.', 'error')
            return redirect(url_for('auth.verify_pending'))
        return f(*args, **kwargs)
    return decorated_function


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        role = request.form.get('role')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return redirect(url_for('auth.register'))

        token = secrets.token_urlsafe(32)

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            is_verified=False,
            verification_token=token
        )
        db.session.add(user)
        db.session.commit()

        verification_url = url_for('auth.verify_email', token=token, _external=True)
        send_verification_email(email, verification_url)

        login_user(user)
        flash('Account created! Check your email to verify your account.', 'success')
        return redirect(url_for('auth.verify_pending'))

    return render_template('auth/register.html')


@auth.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('main.index'))

    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    flash('Email verified! Your account is fully active.', 'success')
    if user.role == 'athlete':
        return redirect(url_for('profile.setup'))
    return redirect(url_for('coach.setup'))


@auth.route('/verify-pending')
@login_required
def verify_pending():
    if current_user.is_verified:
        if current_user.role == 'athlete':
            return redirect(url_for('profile.setup'))
        return redirect(url_for('coach.setup'))
    return render_template('auth/verify_pending.html')


@auth.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        return redirect(url_for('main.index'))

    token = secrets.token_urlsafe(32)
    current_user.verification_token = token
    db.session.commit()

    verification_url = url_for('auth.verify_email', token=token, _external=True)
    success = send_verification_email(current_user.email, verification_url)

    if success:
        flash('Verification email resent! Check your inbox.', 'success')
    else:
        flash('Could not send email. Try again later.', 'error')

    return redirect(url_for('auth.verify_pending'))


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('auth.login'))

        login_user(user)
        return redirect(url_for('main.index'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))