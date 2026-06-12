from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app import db
from app.models import Message, Notification, PersonalBest, AthleteProfile
from sqlalchemy import func

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('index.html')

    ctx = {}

    if current_user.role == 'athlete' and current_user.athlete_profile:
        athlete = current_user.athlete_profile
        all_prs = athlete.personal_bests.all()

        from app.profile import time_to_seconds
        best_by_event = {}
        for pr in all_prs:
            if pr.event not in best_by_event:
                best_by_event[pr.event] = pr
            else:
                if time_to_seconds(pr.time_recorded) < time_to_seconds(best_by_event[pr.event].time_recorded):
                    best_by_event[pr.event] = pr

        recent_pr = athlete.personal_bests.order_by(
            PersonalBest.created_at.desc()
        ).first()

        active_convos = db.session.query(func.count(Message.id)).filter(
            (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id),
            Message.request_status == 'accepted'
        ).scalar() or 0

        unread_notifs = db.session.query(func.count(Notification.id)).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).scalar() or 0

        total_athletes = AthleteProfile.query.count()

        ctx = {
            'total_prs': len(all_prs),
            'total_events': len(best_by_event),
            'best_prs': sorted(best_by_event.values(), key=lambda p: p.event)[:6],
            'recent_pr': recent_pr,
            'active_convos': active_convos,
            'unread_notifs': unread_notifs,
            'total_athletes': total_athletes,
        }

    elif current_user.role == 'coach' and current_user.coach_profile:
        sent_requests = db.session.query(func.count(Message.id)).filter(
            Message.sender_id == current_user.id,
            Message.is_request == True
        ).scalar() or 0

        pending = db.session.query(func.count(Message.id)).filter(
            Message.sender_id == current_user.id,
            Message.request_status == 'pending'
        ).scalar() or 0

        accepted = db.session.query(func.count(Message.id)).filter(
            Message.sender_id == current_user.id,
            Message.request_status == 'accepted'
        ).scalar() or 0

        unread = db.session.query(func.count(Message.id)).filter(
            Message.recipient_id == current_user.id,
            Message.is_read == False,
            Message.request_status == 'accepted'
        ).scalar() or 0

        total_athletes = AthleteProfile.query.count()

        ctx = {
            'sent_requests': sent_requests,
            'pending': pending,
            'accepted': accepted,
            'unread': unread,
            'total_athletes': total_athletes,
        }

    return render_template('index.html', **ctx)


@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@main.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500