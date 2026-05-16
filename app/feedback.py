from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user
from app import db
from app.models import Feedback
from app.email import send_feedback_email

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback', methods=['POST'])
def submit():
    try:
        feedback_type = request.form.get('feedback_type', '').strip()
        message = request.form.get('message', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        page_url = request.form.get('page_url', '').strip()

        if not message or not feedback_type:
            return jsonify({'success': False, 'error': 'Missing fields'}), 400

        feedback = Feedback(
            user_id=current_user.id if current_user.is_authenticated else None,
            feedback_type=feedback_type,
            message=message,
            contact_email=contact_email or None,
            page_url=page_url or None
        )
        db.session.add(feedback)
        db.session.commit()

        send_feedback_email(feedback_type, message, contact_email, page_url,
                           current_user.email if current_user.is_authenticated else 'Anonymous')

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500