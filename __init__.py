"""
Poway Recovery Center API - app setup (same role as Open Coding Society flask __init__.py)

Creates the Flask app, CORS, and database objects that model/ and api/ import.
"""
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy


# Load environment variables from .env, no matter which folder main.py is run from
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Setup of key Flask object (app); instance folder holds the database
app = Flask(__name__, instance_path=os.path.join(basedir, 'instance'))

# Configure Flask Port, default to 8587 which is the same as Open Coding Society flask
app.config['FLASK_PORT'] = int(os.environ.get('FLASK_PORT') or 8587)

# Allowed servers for cross-origin resource sharing (CORS)
allowed_origins = [
    'http://localhost:4000',
    'http://127.0.0.1:4000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://adyashipekar.github.io',  # Deployed GitHub Pages site (poway-recovery-center repo)
]
# Any other deployed frontend(s), comma separated in .env
allowed_origins += [o.strip() for o in (os.environ.get('ALLOWED_ORIGINS') or '').split(',') if o.strip()]

cors = CORS(
    app,
    supports_credentials=True,
    origins=allowed_origins,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# Admin defaults
app.config['ADMIN_USER'] = os.environ.get('ADMIN_USER') or 'Adya Shipekar'
app.config['ADMIN_UID'] = os.environ.get('ADMIN_UID') or 'adyashipekar'
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL') or 'adya.shipekar1@gmail.com'
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD') or os.environ.get('DEFAULT_PASSWORD') or 'password'
# Password given to every other seeded user until they change it on their profile page
app.config['DEFAULT_PASSWORD'] = os.environ.get('DEFAULT_PASSWORD') or 'password'
# Members created on first run: (name, uid, role). Each starting password is read from
# <FIRSTNAME>_PASSWORD in .env (e.g. ANIKA_PASSWORD), falling back to DEFAULT_PASSWORD.
app.config['MEMBERS'] = [
    ('Anika Seksaria', 'anikaseksaria', 'Admin'),
    ('Jailene Tang', 'jailenetang', 'Admin'),
    ('Joan Kim', 'joankim', 'User'),
    ('Ainsley Albert', 'ainsleyalbert', 'User'),
    ('Samanvi Yachareni', 'samanviyachareni', 'User'),
]

# Browser settings
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'prc-flask-secret-key-set-SECRET_KEY-in-env'
app.config['JWT_TOKEN_NAME'] = os.environ.get('JWT_TOKEN_NAME') or 'jwt_python_flask'
app.config['JWT_TOKEN_MAX_AGE'] = int(os.environ.get('JWT_TOKEN_MAX_AGE') or 604800)  # 1 week
# Production = frontend on GitHub Pages + backend on its own HTTPS domain,
# which needs SameSite=None; Secure cookies (same switch OCS uses)
app.config['IS_PRODUCTION'] = (os.environ.get('IS_PRODUCTION') or 'false').lower() == 'true'

# Database settings - SQLite in instance/volumes/ (OCS layout)
dbName = 'user_management'
os.makedirs(os.path.join(app.instance_path, 'volumes'), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(app.instance_path, 'volumes', dbName + '.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
