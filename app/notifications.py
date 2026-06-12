from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/notifications')
@login_required
def index():
    # Mark read first, then fetch — single transaction
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})

    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()

    db.session.commit()

    return render_template('notifications/index.html', notifications=notifs)


@notifications_bp.route('/notifications/count')
@login_required
def count():
    from sqlalchemy import func
    n = db.session.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).scalar() or 0
    return jsonify({'count': n})