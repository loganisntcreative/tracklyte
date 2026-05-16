import os
import sendgrid
from sendgrid.helpers.mail import Mail


def send_verification_email(to_email, token):
    app_url = os.environ.get('APP_URL', 'http://127.0.0.1:5000')
    verification_url = f"{app_url}/verify/{token}"

    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = os.environ.get('SENDGRID_FROM_EMAIL')

    html_content = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
        <h1 style="font-size: 24px; font-weight: 600; color: #111; margin-bottom: 8px;">Verify your email</h1>
        <p style="color: #555; font-size: 15px; line-height: 1.6; margin-bottom: 32px;">
            Welcome to TrackLyte! Click the button below to verify your email address and activate your account.
        </p>
        <a href="{verification_url}"
            style="background: #1D9E75; color: white; padding: 12px 28px; border-radius: 8px;
                   text-decoration: none; font-weight: 500; font-size: 15px; display: inline-block;">
            Verify my email
        </a>
        <p style="color: #999; font-size: 13px; margin-top: 32px;">
            If you didn't create a TrackLyte account, you can safely ignore this email.
        </p>
        <p style="color: #bbb; font-size: 12px; margin-top: 8px;">
            Or copy this link: {verification_url}
        </p>
    </div>
    """

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Verify your TrackLyte account',
        html_content=html_content
    )

    try:
        sg.send(message)
        return True
    except Exception as e:
        print(f'Email send error: {e}')
        return False

def send_feedback_email(feedback_type, message, contact_email, page_url, user_email):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = os.environ.get('SENDGRID_FROM_EMAIL')

    type_emoji = {'bug': '🐛', 'suggestion': '💡', 'compliment': '⭐'}.get(feedback_type, '📩')

    html_content = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px 20px;">
        <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 4px;">
            {type_emoji} New {feedback_type} on TrackLyte
        </h2>
        <p style="color: #6B7280; font-size: 13px; margin-bottom: 24px;">Someone just submitted feedback</p>
        <div style="background: #F9FAFB; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <p style="font-size: 15px; color: #111; line-height: 1.6; margin: 0;">{message}</p>
        </div>
        <table style="width: 100%; font-size: 13px; color: #6B7280;">
            <tr><td style="padding: 4px 0;"><strong>User:</strong></td><td>{user_email}</td></tr>
            <tr><td style="padding: 4px 0;"><strong>Contact:</strong></td><td>{contact_email or 'Not provided'}</td></tr>
            <tr><td style="padding: 4px 0;"><strong>Page:</strong></td><td>{page_url or 'Not provided'}</td></tr>
            <tr><td style="padding: 4px 0;"><strong>Type:</strong></td><td>{feedback_type}</td></tr>
        </table>
    </div>
    """

    mail = Mail(
        from_email=from_email,
        to_emails=from_email,
        subject=f'[TrackLyte] {type_emoji} New {feedback_type}',
        html_content=html_content
    )

    try:
        sg.send(mail)
        return True
    except Exception as e:
        print(f'Feedback email error: {e}')
        return False