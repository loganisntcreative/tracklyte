from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import CoachProfile
from app.auth import verified_required
from app.utils import upload_photo

coach_bp = Blueprint('coach', __name__)

US_STATES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
    'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
    'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
    'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
]

DIVISION_LEVELS = [
    'NCAA Division I', 'NCAA Division II', 'NCAA Division III',
    'NAIA', 'NJCAA', 'High School', 'Club / AAU', 'Other'
]


@coach_bp.route('/coach/setup', methods=['GET', 'POST'])
@login_required
@verified_required
def setup():
    if current_user.role != 'coach':
        return redirect(url_for('main.index'))
    if current_user.coach_profile:
        return redirect(url_for('coach.view'))

    if request.method == 'POST':
        photo_url = upload_photo(request.files.get('photo'))
        coach = CoachProfile(
            user_id=current_user.id,
            first_name=request.form.get('first_name', '').strip(),
            last_name=request.form.get('last_name', '').strip(),
            school=request.form.get('school', '').strip(),
            college=request.form.get('college', '').strip(),
            state=request.form.get('state', '').strip(),
            bio=request.form.get('bio', '').strip(),
            photo_url=photo_url
        )
        db.session.add(coach)
        db.session.commit()
        flash('Coach profile created! Welcome to TrackLyte.', 'success')
        return redirect(url_for('coach.view'))

    return render_template('coach/setup.html', states=US_STATES,
                           divisions=DIVISION_LEVELS)


@coach_bp.route('/coach/profile')
@login_required
def view():
    if current_user.role != 'coach':
        return redirect(url_for('main.index'))
    if not current_user.coach_profile:
        return redirect(url_for('coach.setup'))

    coach = current_user.coach_profile
    return render_template('coach/view.html', coach=coach)


@coach_bp.route('/coach/profile/edit', methods=['GET', 'POST'])
@login_required
@verified_required
def edit():
    if current_user.role != 'coach':
        return redirect(url_for('main.index'))
    coach = current_user.coach_profile
    if not coach:
        return redirect(url_for('coach.setup'))

    if request.method == 'POST':
        coach.first_name = request.form.get('first_name', '').strip()
        coach.last_name = request.form.get('last_name', '').strip()
        coach.school = request.form.get('school', '').strip()
        coach.college = request.form.get('college', '').strip()
        coach.state = request.form.get('state', '').strip()
        coach.bio = request.form.get('bio', '').strip()

        new_photo = upload_photo(request.files.get('photo'))
        if new_photo:
            coach.photo_url = new_photo

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('coach.view'))

    return render_template('coach/edit.html', coach=coach, states=US_STATES,
                           divisions=DIVISION_LEVELS)