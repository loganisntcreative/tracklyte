from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db, cache
from app.models import PersonalBest
from app.auth import verified_required
from datetime import date
import cloudinary
import cloudinary.uploader
import os

prs_bp = Blueprint('prs', __name__)

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

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

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@prs_bp.route('/prs/add', methods=['GET', 'POST'])
@login_required
@verified_required
def add():
    if current_user.role != 'athlete':
        return redirect(url_for('main.index'))
    if not current_user.athlete_profile:
        return redirect(url_for('profile.setup'))

    if request.method == 'POST':
        media_url = None
        media_type = None

        file = request.files.get('media')
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            resource_type = 'video' if ext in {'mp4', 'mov', 'avi'} else 'image'
            try:
                result = cloudinary.uploader.upload(
                    file,
                    resource_type=resource_type,
                    folder='tracklyte'
                )
                media_url = result['secure_url']
                media_type = 'video' if resource_type == 'video' else 'image'
            except Exception as e:
                flash(f'Media upload failed: {str(e)}', 'error')
                return redirect(url_for('prs.add'))

        pr = PersonalBest(
            athlete_id=current_user.athlete_profile.id,
            event=request.form.get('event'),
            time_recorded=request.form.get('time_recorded', '').strip(),
            date_achieved=date.fromisoformat(request.form.get('date_achieved')) if request.form.get('date_achieved') else None,
            meet_name=request.form.get('meet_name', '').strip() or None,
            media_url=media_url,
            media_type=media_type
        )
        db.session.add(pr)
        db.session.commit()
        cache.clear()
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
@verified_required
def delete(pr_id):
    pr = PersonalBest.query.get_or_404(pr_id)
    if pr.athlete.user_id != current_user.id:
        flash('Not allowed.', 'error')
        return redirect(url_for('prs.history'))
    db.session.delete(pr)
    db.session.commit()
    cache.clear()
    flash('PR deleted.', 'success')
    return redirect(url_for('prs.history'))