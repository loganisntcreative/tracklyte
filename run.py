from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1 day

if __name__ == '__main__':
    app.run(debug=False)