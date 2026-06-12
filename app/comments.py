from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Comment, PersonalBest, Notification
from app.profanity import contains_profanity, contains_borderline

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/comments/<int:pr_id>', methods=['POST'])
@login_required
def add_comment(pr_id):
    pr = PersonalBest.query.get_or_404(pr_id)
    body = request.form.get('body', '').strip()
    confirmed = request.form.get('confirmed', 'false') == 'true'

    if not body:
        return jsonify({'success': False, 'error': 'Empty comment'}), 400
    if len(body) > 300:
        return jsonify({'success': False, 'error': 'Too long'}), 400
    if contains_profanity(body):
        return jsonify({'success': False, 'error': 'Please keep comments respectful'}), 400
    if contains_borderline(body) and not confirmed:
        return jsonify({'success': False, 'confirm': True,
                        'warning': 'Your comment may come across as negative. Are you sure?'}), 200

    if current_user.role == 'coach' and current_user.coach_profile:
        name = f'{current_user.coach_profile.first_name} {current_user.coach_profile.last_name}'
        photo = current_user.coach_profile.photo_url or ''
    elif current_user.athlete_profile:
        name = f'{current_user.athlete_profile.first_name} {current_user.athlete_profile.last_name}'
        photo = current_user.athlete_profile.photo_url or ''
    else:
        name = current_user.email
        photo = ''

    comment = Comment(pr_id=pr_id, user_id=current_user.id, body=body)
    db.session.add(comment)

    athlete_user_id = pr.athlete.user_id
    if athlete_user_id != current_user.id:
        notif = Notification(
            user_id=athlete_user_id,
            notif_type='comment',
            message=f'{name} commented on your {pr.event} PR',
            link=f'/athlete/{pr.athlete_id}'
        )
        db.session.add(notif)

    db.session.commit()  # ONE commit for both comment and notification

    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'body': comment.body,
            'name': name,
            'photo': photo,
            'time': 'Just now'
        }
    })


@comments_bp.route('/comments/<int:pr_id>', methods=['GET'])
@login_required
def get_comments(pr_id):
    comments = Comment.query.filter_by(pr_id=pr_id).order_by(Comment.created_at.asc()).all()
    result = []
    for c in comments:
        if c.user.role == 'coach' and c.user.coach_profile:
            name = f'{c.user.coach_profile.first_name} {c.user.coach_profile.last_name}'
            photo = c.user.coach_profile.photo_url or ''
            role = 'Coach'
        elif c.user.athlete_profile:
            name = f'{c.user.athlete_profile.first_name} {c.user.athlete_profile.last_name}'
            photo = c.user.athlete_profile.photo_url or ''
            role = 'Athlete'
        else:
            name = c.user.email
            photo = ''
            role = ''
        result.append({
            'id': c.id,
            'body': c.body,
            'name': name,
            'photo': photo,
            'role': role,
            'time': c.created_at.strftime('%b %d, %Y')
        })
    return jsonify(result)


@comments_bp.route('/comments/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        return jsonify({'success': False}), 403
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'success': True})