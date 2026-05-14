from flask import Blueprint, render_template
from flask_login import current_user

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@main.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500