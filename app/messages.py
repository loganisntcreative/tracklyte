from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Message, User, AthleteProfile, CoachProfile
from datetime import datetime

messages_bp = Blueprint('messages', __name__)

STARTERS = [
    "I've been following your progress and I'm impressed with your times.",
    "I coach at [school] and I think you could be a great fit for our program.",
    "I'd love to learn more about your athletic goals and future plans.",
    "Your recent PRs caught my attention — I'd love to connect.",
]


def get_unread_count(user_id):
    return Message.query.filter_by(
        recipient_id=user_id,
        is_read=False,
        request_status='accepted'
    ).count()


def get_request_count(user_id):
    return Message.query.filter_by(
        recipient_id=user_id,
        is_request=True,
        request_status='pending'
    ).count()


@messages_bp.route('/messages')
@login_required
def inbox():
    accepted_messages = Message.query.filter(
        (Message.sender_id == current_user.id) |
        (Message.recipient_id == current_user.id)
    ).filter(
        Message.request_status == 'accepted'
    ).order_by(Message.timestamp.desc()).all()

    conversations = {}
    for msg in accepted_messages:
        other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        if other_id not in conversations:
            other_user = User.query.get(other_id)
            unread = Message.query.filter_by(
                sender_id=other_id,
                recipient_id=current_user.id,
                is_read=False,
                request_status='accepted'
            ).count()
            conversations[other_id] = {
                'user': other_user,
                'last_message': msg,
                'unread': unread
            }

    pending_count = get_request_count(current_user.id)

    return render_template('messages/inbox.html',
                           conversations=conversations.values(),
                           pending_count=pending_count)


@messages_bp.route('/messages/requests')
@login_required
def requests():
    pending = Message.query.filter_by(
        recipient_id=current_user.id,
        is_request=True,
        request_status='pending'
    ).order_by(Message.timestamp.desc()).all()

    return render_template('messages/requests.html', pending=pending)


@messages_bp.route('/messages/requests/<int:msg_id>/accept', methods=['POST'])
@login_required
def accept_request(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.recipient_id != current_user.id:
        flash('Not allowed.', 'error')
        return redirect(url_for('messages.requests'))

    msg.request_status = 'accepted'
    msg.is_request = False
    msg.is_read = True
    db.session.commit()
    flash('Message request accepted!', 'success')
    return redirect(url_for('messages.conversation', other_id=msg.sender_id))


@messages_bp.route('/messages/requests/<int:msg_id>/decline', methods=['POST'])
@login_required
def decline_request(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if msg.recipient_id != current_user.id:
        flash('Not allowed.', 'error')
        return redirect(url_for('messages.requests'))

    msg.request_status = 'declined'
    db.session.commit()
    return redirect(url_for('messages.requests'))


@messages_bp.route('/messages/send/<int:recipient_id>', methods=['GET', 'POST'])
@login_required
def send_request(recipient_id):
    recipient = User.query.get_or_404(recipient_id)

    existing = Message.query.filter_by(
        sender_id=current_user.id,
        recipient_id=recipient_id
    ).first()
    if existing:
        flash('You already sent a message to this person.', 'error')
        return redirect(url_for('discover.athlete_profile',
                                athlete_id=recipient.athlete_profile.id if recipient.athlete_profile else 0))

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
        return redirect(url_for('main.index'))

    return render_template('messages/send.html',
                           recipient=recipient,
                           starters=STARTERS)


@messages_bp.route('/messages/conversation/<int:other_id>', methods=['GET', 'POST'])
@login_required
def conversation(other_id):
    other_user = User.query.get_or_404(other_id)

    accepted = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == other_id)) |
        ((Message.sender_id == other_id) & (Message.recipient_id == current_user.id))
    ).filter(Message.request_status == 'accepted').first()

    if not accepted:
        flash('No active conversation found.', 'error')
        return redirect(url_for('messages.inbox'))

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
        return redirect(url_for('messages.conversation', other_id=other_id))

    messages_list = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == other_id)) |
        ((Message.sender_id == other_id) & (Message.recipient_id == current_user.id))
    ).filter(
        Message.request_status == 'accepted'
    ).order_by(Message.timestamp.asc()).all()

    Message.query.filter_by(
        sender_id=other_id,
        recipient_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return render_template('messages/conversation.html',
                           other_user=other_user,
                           messages_list=messages_list)