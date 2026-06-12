from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Message, User, AthleteProfile, CoachProfile, Notification
from app.profanity import contains_profanity
from datetime import datetime
from sqlalchemy import func

messages_bp = Blueprint('messages', __name__)

STARTERS = [
    "I've been following your progress and I'm impressed with your times.",
    "I coach at [school] and I think you could be a great fit for our program.",
    "I'd love to learn more about your athletic goals and future plans.",
    "Your recent PRs caught my attention — I'd love to connect.",
]


@messages_bp.route('/messages/badge')
@login_required
def badge():
    unread = db.session.query(func.count(Message.id)).filter(
        Message.recipient_id == current_user.id,
        Message.is_read == False,
        Message.request_status == 'accepted'
    ).scalar() or 0

    pending = db.session.query(func.count(Message.id)).filter(
        Message.recipient_id == current_user.id,
        Message.is_request == True,
        Message.request_status == 'pending'
    ).scalar() or 0

    return jsonify({'count': unread + pending})


@messages_bp.route('/messages')
@login_required
def inbox():
    try:
        accepted_messages = Message.query.filter(
            (Message.sender_id == current_user.id) |
            (Message.recipient_id == current_user.id)
        ).filter(
            Message.request_status == 'accepted'
        ).order_by(Message.timestamp.desc()).all()

        # Collect all partner IDs upfront
        partner_ids = set()
        for msg in accepted_messages:
            other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
            partner_ids.add(other_id)

        # Load all partner users in ONE query instead of one per conversation
        users_map = {u.id: u for u in User.query.filter(User.id.in_(partner_ids)).all()} if partner_ids else {}

        # Get unread counts for all senders in ONE query
        unread_rows = db.session.query(
            Message.sender_id,
            func.count(Message.id)
        ).filter(
            Message.recipient_id == current_user.id,
            Message.is_read == False,
            Message.request_status == 'accepted'
        ).group_by(Message.sender_id).all()
        unread_counts = {sender_id: cnt for sender_id, cnt in unread_rows}

        conversations = {}
        for msg in accepted_messages:
            other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
            if other_id not in conversations:
                conversations[other_id] = {
                    'user': users_map.get(other_id),
                    'last_message': msg,
                    'unread': unread_counts.get(other_id, 0)
                }

        sent_pending = Message.query.filter_by(
            sender_id=current_user.id,
            request_status='pending'
        ).order_by(Message.timestamp.desc()).all()

        pending_count = db.session.query(func.count(Message.id)).filter(
            Message.recipient_id == current_user.id,
            Message.is_request == True,
            Message.request_status == 'pending'
        ).scalar() or 0

        return render_template('messages/inbox.html',
                               conversations=conversations.values(),
                               sent_pending=sent_pending,
                               pending_count=pending_count)
    except Exception as e:
        flash(f'Could not load messages: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@messages_bp.route('/messages/requests')
@login_required
def message_requests():
    try:
        pending = Message.query.filter_by(
            recipient_id=current_user.id,
            is_request=True,
            request_status='pending'
        ).order_by(Message.timestamp.desc()).all()
        return render_template('messages/requests.html', pending=pending)
    except Exception as e:
        flash(f'Could not load requests: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@messages_bp.route('/messages/requests/<int:msg_id>/accept', methods=['POST'])
@login_required
def accept_request(msg_id):
    try:
        msg = Message.query.get_or_404(msg_id)
        if msg.recipient_id != current_user.id:
            flash('Not allowed.', 'error')
            return redirect(url_for('messages.message_requests'))
        msg.request_status = 'accepted'
        msg.is_request = False
        msg.is_read = True
        db.session.commit()
        flash('Message request accepted!', 'success')
        return redirect(url_for('messages.conversation', other_id=msg.sender_id))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('messages.message_requests'))


@messages_bp.route('/messages/requests/<int:msg_id>/decline', methods=['POST'])
@login_required
def decline_request(msg_id):
    try:
        msg = Message.query.get_or_404(msg_id)
        if msg.recipient_id != current_user.id:
            flash('Not allowed.', 'error')
            return redirect(url_for('messages.message_requests'))
        msg.request_status = 'declined'
        db.session.commit()
        return redirect(url_for('messages.message_requests'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('messages.message_requests'))


@messages_bp.route('/messages/send/<int:recipient_id>', methods=['GET', 'POST'])
@login_required
def send_request(recipient_id):
    try:
        recipient = User.query.get_or_404(recipient_id)
        existing = Message.query.filter_by(
            sender_id=current_user.id,
            recipient_id=recipient_id
        ).first()
        if existing:
            flash('You already sent a message to this person.', 'error')
            return redirect(url_for('main.index'))

        if request.method == 'POST':
            body = request.form.get('body', '').strip()
            if not body:
                flash('Message cannot be empty.', 'error')
                return redirect(url_for('messages.send_request', recipient_id=recipient_id))
            if len(body) > 500:
                flash('Message must be under 500 characters.', 'error')
                return redirect(url_for('messages.send_request', recipient_id=recipient_id))
            msg = Message(
                sender_id=current_user.id,
                recipient_id=recipient_id,
                body=body,
                is_request=True,
                request_status='pending'
            )
            db.session.add(msg)
            db.session.commit()
            flash('Message request sent!', 'success')
            return redirect(url_for('messages.inbox'))

        return render_template('messages/send.html', recipient=recipient, starters=STARTERS)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@messages_bp.route('/messages/conversation/<int:other_id>', methods=['GET', 'POST'])
@login_required
def conversation(other_id):
    try:
        other_user = User.query.get_or_404(other_id)

        if request.method == 'POST':
            body = request.form.get('body', '').strip()
            if body:
                msg = Message(
                    sender_id=current_user.id,
                    recipient_id=other_id,
                    body=body,
                    is_request=False,
                    request_status='accepted'
                )
                db.session.add(msg)
                db.session.commit()
            return ('', 204)

        # Single query — if empty, no active conversation
        messages_list = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == other_id)) |
            ((Message.sender_id == other_id) & (Message.recipient_id == current_user.id))
        ).filter(
            Message.request_status == 'accepted'
        ).order_by(Message.timestamp.asc()).all()

        if not messages_list:
            flash('No active conversation found.', 'error')
            return redirect(url_for('messages.inbox'))

        # Mark as read
        Message.query.filter_by(
            sender_id=other_id,
            recipient_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()

        return render_template('messages/conversation.html',
                               other_user=other_user,
                               messages_list=messages_list)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('messages.inbox'))


@messages_bp.route('/messages/poll/<int:other_id>')
@login_required
def poll(other_id):
    try:
        since = request.args.get('since', 0, type=float)
        since_dt = datetime.utcfromtimestamp(since)

        new_messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == other_id)) |
            ((Message.sender_id == other_id) & (Message.recipient_id == current_user.id))
        ).filter(
            Message.request_status == 'accepted',
            Message.timestamp > since_dt
        ).order_by(Message.timestamp.asc()).all()

        Message.query.filter_by(
            sender_id=other_id,
            recipient_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()

        return jsonify([{
            'id': m.id,
            'body': m.body,
            'sender_id': m.sender_id,
            'is_mine': m.sender_id == current_user.id,
            'timestamp': m.timestamp.strftime('%b %d, %Y %H:%M:%S'),
            'is_read': m.is_read
        } for m in new_messages])
    except Exception:
        return jsonify([])