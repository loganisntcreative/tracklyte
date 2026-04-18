from app import cache
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import PersonalBest
from datetime import date

prs_bp = Blueprint('prs', __name__)

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

@prs_bp.route('/prs/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role != 'athlete':
        return redirect(url_for('main.index'))
    if not current_user.athlete_profile:
        return redirect(url_for('profile.setup'))

    if request.method == 'POST':
        pr = PersonalBest(
            athlete_id=current_user.athlete_profile.id,
            event=request.form.get('event'),
            time_recorded=request.form.get('time_recorded', '').strip(),
            date_achieved=date.fromisoformat(request.form.get('date_achieved')) if request.form.get('date_achieved') else None,
            meet_name=request.form.get('meet_name', '').strip() or None
        )
        db.session.add(pr)
        db.session.commit()
        flash('PR logged!', 'success')
        return redirect(url_for('prs.history'))

    return render_template('prs/add.html', events=TRACK_EVENTS, today=date.today().isoformat())


@prs_bp.route('/prs')
@login_required
def history():
    if current_user.role != 'athlete':
        return redirect(url_for('main.index'))
    if not current_user.athlete_profile:
        return redirect(url_for('profile.setup'))

    athlete = current_user.athlete_profile
    all_prs = athlete.personal_bests.order_by(PersonalBest.date_achieved.desc()).all()

    grouped = {}
    for pr in all_prs:
        grouped.setdefault(pr.event, []).append(pr)

    return render_template('prs/history.html', grouped=grouped, total=len(all_prs))


@prs_bp.route('/prs/delete/<int:pr_id>', methods=['POST'])
@login_required
def delete(pr_id):
    pr = PersonalBest.query.get_or_404(pr_id)
    if pr.athlete.user_id != current_user.id:
        flash('Not allowed.', 'error')
        return redirect(url_for('prs.history'))
    db.session.delete(pr)
    db.session.commit()
    flash('PR deleted.', 'success')
    return redirect(url_for('prs.history'))