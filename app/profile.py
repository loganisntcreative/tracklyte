from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db, cache
from app.models import AthleteProfile, PersonalBest
from app.auth import verified_required
import json

profile_bp = Blueprint('profile', __name__)

TRACK_EVENTS = [
    '100m', '200m', '400m', '800m', '1500m', 'Mile',
    '3000m', '5000m', '10000m',
    '100m Hurdles', '110m Hurdles', '400m Hurdles',
    '3000m Steeplechase',
    '4x100m Relay', '4x400m Relay',
    'High Jump', 'Long Jump', 'Triple Jump', 'Pole Vault',
    'Shot Put', 'Discus', 'Javelin', 'Hammer',
    'Heptathlon', 'Decathlon'
]

US_STATES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
    'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
    'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
    'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
]

def build_chart_data(athlete):
    all_prs = athlete.personal_bests.filter(
        PersonalBest.date_achieved != None
    ).order_by(PersonalBest.date_achieved.asc()).all()

    grouped = {}
    for pr in all_prs:
        grouped.setdefault(pr.event, []).append(pr)

    charts = {}
    for event, prs in grouped.items():
        if len(prs) < 2:
            continue
        charts[event] = {
            'labels': [pr.date_achieved.strftime('%b %d, %Y') for pr in prs],
            'values': [pr.time_recorded for pr in prs]
        }
    return json.dumps(charts)


@profile_bp.route('/profile/setup', methods=['GET', 'POST'])
@login_required
@verified_required
def setup():
    if current_user.role != 'athlete':
        return redirect(url_for('main.index'))
    if current_user.athlete_profile:
        return redirect(url_for('profile.view'))

    if request.method == 'POST':
        selected_events = ','.join(request.form.getlist('events'))
        athlete = AthleteProfile(
            user_id=current_user.id,
            first_name=request.form.get('first_name', '').strip(),
            last_name=request.form.get('last_name', '').strip(),
            school=request.form.get('school', '').strip(),
            grad_year=int(request.form.get('grad_year')),
            state=request.form.get('state', '').strip(),
            events=selected_events,
            bio=request.form.get('bio', '').strip()
        )
        db.session.add(athlete)
        db.session.commit()
        cache.clear()
        flash('Profile created! Welcome to TrackLyte.', 'success')
        return redirect(url_for('profile.view'))

    current_year = 2025
    grad_years = list(range(current_year, current_year + 5))
    return render_template('profile/setup.html', events=TRACK_EVENTS, states=US_STATES, grad_years=grad_years)


@profile_bp.route('/profile')
@login_required
def view():
    if current_user.role != 'athlete':
        return redirect(url_for('main.index'))
    if not current_user.athlete_profile:
        return redirect(url_for('profile.setup'))

    athlete = current_user.athlete_profile
    athlete_events = athlete.events.split(',') if athlete.events else []
    chart_data = build_chart_data(athlete)
    return render_template('profile/view.html', athlete=athlete,
                           athlete_events=athlete_events, chart_data=chart_data)


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@verified_required
def edit():
    if current_user.role != 'athlete':
        return redirect(url_for('main.index'))
    athlete = current_user.athlete_profile
    if not athlete:
        return redirect(url_for('profile.setup'))

    if request.method == 'POST':
        athlete.first_name = request.form.get('first_name', '').strip()
        athlete.last_name = request.form.get('last_name', '').strip()
        athlete.school = request.form.get('school', '').strip()
        athlete.grad_year = int(request.form.get('grad_year'))
        athlete.state = request.form.get('state', '').strip()
        athlete.events = ','.join(request.form.getlist('events'))
        athlete.bio = request.form.get('bio', '').strip()
        db.session.commit()
        cache.clear()
        flash('Profile updated!', 'success')
        return redirect(url_for('profile.view'))

    current_events = athlete.events.split(',') if athlete.events else []
    current_year = 2025
    grad_years = list(range(current_year, current_year + 5))
    return render_template('profile/edit.html', athlete=athlete, events=TRACK_EVENTS,
                           current_events=current_events, states=US_STATES, grad_years=grad_years)