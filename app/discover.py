from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import AthleteProfile, PersonalBest
from app import cache, db
from app.profile import build_chart_data, time_to_seconds, get_best_prs
import json

discover_bp = Blueprint('discover', __name__)

TRACK_EVENTS = [
    '100m', '200m', '400m', '800m', '1500m', 'Mile',
    '3000m', '5000m', '10000m',
    '100m Hurdles', '110m Hurdles', '300m Hurdles', '400m Hurdles',
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
    # Use role instead of user_id — all coaches share one cache, all athletes share another
    return f"discover_{current_user.role}_{request.query_string.decode()}"


@discover_bp.route('/discover/search')
@login_required
def search():
    query = request.args.get('q', '').strip().lower()
    if len(query) < 2:
        return jsonify([])

    all_athletes = AthleteProfile.query.all()
    matched = []
    for a in all_athletes:
        full_name = f'{a.first_name} {a.last_name}'.lower()
        if query in full_name or query in a.first_name.lower() or query in a.last_name.lower():
            matched.append(a)
        if len(matched) >= 10:
            break

    return jsonify([{
        'id': a.id,
        'name': f'{a.first_name} {a.last_name}',
        'school': a.school or '',
        'grad_year': a.grad_year or '',
        'state': a.state or '',
        'photo_url': a.photo_url or ''
    } for a in matched])


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

    if athletes:
        athlete_ids = [a.id for a in athletes]

        # ONE bulk query for ALL athlete PRs — eliminates N+1
        pr_query = PersonalBest.query.filter(
            PersonalBest.athlete_id.in_(athlete_ids)
        )
        if event_filter:
            pr_query = pr_query.filter(PersonalBest.event == event_filter)

        all_prs = pr_query.all()

        # Build best PR map in Python — O(n) single pass
        best_prs_map = {}
        for pr in all_prs:
            aid = pr.athlete_id
            if aid not in best_prs_map:
                best_prs_map[aid] = pr
            else:
                if time_to_seconds(pr.time_recorded) < time_to_seconds(best_prs_map[aid].time_recorded):
                    best_prs_map[aid] = pr
    else:
        best_prs_map = {}

    athlete_data = []
    for athlete in athletes:
        events_list = athlete.events.split(',') if athlete.events else []
        best_pr = best_prs_map.get(athlete.id)
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
@cache.cached(timeout=120, key_prefix=lambda: f"athlete_{request.view_args['athlete_id']}")
def athlete_profile(athlete_id):
    athlete = AthleteProfile.query.get_or_404(athlete_id)
    events_list = athlete.events.split(',') if athlete.events else []

    # Load PRs ONCE — pass to both functions
    all_prs = athlete.personal_bests.all()
    grouped_prs = {}
    for pr in all_prs:
        grouped_prs.setdefault(pr.event, []).append(pr)

    chart_data = build_chart_data(athlete, prs=all_prs)

    return render_template(
        'discover/athlete.html',
        athlete=athlete,
        events_list=events_list,
        grouped_prs=grouped_prs,
        chart_data=chart_data
    )