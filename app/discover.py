from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models import AthleteProfile, PersonalBest
from app import cache
from app.profile import build_chart_data
import json

discover_bp = Blueprint('discover', __name__)

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

GRAD_YEARS = list(range(2025, 2030))


def discover_cache_key():
    return f"discover_{current_user.id}_{request.query_string.decode()}"


def time_to_seconds(t):
    if not t:
        return float('inf')
    t = t.strip()
    try:
        if ':' in t:
            parts = t.split(':')
            return float(parts[0]) * 60 + float(parts[1])
        return float(t.replace('-', '.').replace("'", '.'))
    except Exception:
        return float('inf')


@discover_bp.route('/discover')
@login_required
@cache.cached(timeout=300, key_prefix=discover_cache_key)
def index():
    event_filter = request.args.get('event', '').strip()
    year_filter = request.args.get('grad_year', '').strip()
    state_filter = request.args.get('state', '').strip()

    query = AthleteProfile.query

    if year_filter:
        query = query.filter(AthleteProfile.grad_year == int(year_filter))
    if state_filter:
        query = query.filter(AthleteProfile.state == state_filter)
    if event_filter:
        query = query.filter(AthleteProfile.events.contains(event_filter))

    athletes = query.order_by(AthleteProfile.last_name).all()

    athlete_data = []
    for athlete in athletes:
        events_list = athlete.events.split(',') if athlete.events else []
        best_pr = (
            athlete.personal_bests
            .filter(PersonalBest.event == event_filter)
            .order_by(PersonalBest.date_achieved.desc())
            .first()
        ) if event_filter else (
            athlete.personal_bests
            .order_by(PersonalBest.date_achieved.desc())
            .first()
        )
        athlete_data.append({
            'athlete': athlete,
            'events_list': events_list,
            'best_pr': best_pr,
            'sort_time': time_to_seconds(best_pr.time_recorded) if best_pr else float('inf')
        })

    athlete_data.sort(key=lambda x: x['sort_time'])

    return render_template(
        'discover/index.html',
        athlete_data=athlete_data,
        events=TRACK_EVENTS,
        states=US_STATES,
        grad_years=GRAD_YEARS,
        event_filter=event_filter,
        year_filter=year_filter,
        state_filter=state_filter,
        result_count=len(athletes)
    )


@discover_bp.route('/athlete/<int:athlete_id>')
@login_required
def athlete_profile(athlete_id):
    athlete = AthleteProfile.query.get_or_404(athlete_id)
    events_list = athlete.events.split(',') if athlete.events else []

    all_prs = athlete.personal_bests.order_by(PersonalBest.date_achieved.desc()).all()
    grouped_prs = {}
    for pr in all_prs:
        grouped_prs.setdefault(pr.event, []).append(pr)

    chart_data = build_chart_data(athlete)

    return render_template(
        'discover/athlete.html',
        athlete=athlete,
        events_list=events_list,
        grouped_prs=grouped_prs,
        chart_data=chart_data
    )