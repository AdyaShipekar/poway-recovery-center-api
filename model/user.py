""" User model and default users (same role as Open Coding Society flask model/user.py) """
import os
import re
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from __init__ import app, db


EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_PATTERN = re.compile(r'^\+?[\d\s().-]{7,20}$')
UID_PATTERN = re.compile(r'^[A-Za-z0-9._-]{3,40}$')


class User(db.Model):
    """
    User Model

    Attributes:
        id (Column): Primary key.
        _name (Column): The user's full name.
        _uid (Column): Unique username, used to log in.
        _email (Column): Optional unique email address, can also be used to log in.
        _phone (Column): Optional phone number.
        _password (Column): Hashed password.
        _role (Column): "User" or "Admin".
        token_version (Column): Bumped on password change so older login tokens stop working.
        created_at (Column): When the account was created.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column(db.String(255), unique=False, nullable=False)
    _uid = db.Column(db.String(255), unique=True, nullable=False)
    _email = db.Column(db.String(255), unique=True, nullable=True)
    _phone = db.Column(db.String(32), unique=False, nullable=True)
    _password = db.Column(db.String(255), unique=False, nullable=False)
    _role = db.Column(db.String(20), default="User", nullable=False)
    token_version = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, name, uid, password=None, email=None, phone=None, role="User"):
        self._name = name
        self._uid = uid.strip().lower()
        self._email = email.strip().lower() if email else None
        self._phone = phone.strip() if phone else None
        self._role = role
        self.token_version = 0
        self.set_password(password or app.config['DEFAULT_PASSWORD'])

    @property
    def name(self):
        return self._name

    @property
    def uid(self):
        return self._uid

    @property
    def email(self):
        return self._email

    @property
    def phone(self):
        return self._phone

    @property
    def role(self):
        return self._role

    def is_admin(self):
        return self._role == "Admin"

    def set_password(self, password):
        """ Hash the password and invalidate any login tokens issued before the change """
        self._password = generate_password_hash(password, "pbkdf2:sha256", salt_length=10)
        self.token_version = (self.token_version or 0) + 1

    def is_password(self, password):
        return check_password_hash(self._password, password)

    @staticmethod
    def validate(name=None, uid=None, email=None, phone=None, password=None):
        """ Returns an error message for the first invalid field supplied, or None """
        if name is not None and not name.strip():
            return 'Name is required'
        if uid is not None and not UID_PATTERN.match(uid.strip()):
            return 'Username must be 3-40 letters, numbers, dots, dashes or underscores'
        if email and not EMAIL_PATTERN.match(email.strip()):
            return 'Please enter a valid email address'
        if phone and not PHONE_PATTERN.match(phone.strip()):
            return 'Please enter a valid phone number'
        if password is not None and len(password) < 6:
            return 'Password must be at least 6 characters'
        return None

    def create(self):
        """ Add the user to the database; returns None if the username or email is taken """
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def read(self):
        return {
            "id": self.id,
            "name": self.name,
            "uid": self.uid,
            "email": self.email or "",
            "phone": self.phone or "",
            "role": self.role,
            "is_admin": self.is_admin(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def update(self, inputs):
        """ Update name, email and/or phone from a dict; returns None if the email is taken """
        if 'name' in inputs:
            self._name = inputs['name'].strip()
        if 'email' in inputs:
            self._email = inputs['email'].strip().lower() or None
        if 'phone' in inputs:
            self._phone = inputs['phone'].strip() or None
        try:
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def delete(self):
        db.session.delete(self)
        db.session.commit()


def initUsers():
    """
    Create the database tables and the default users.
    New users are created with their starting password; existing users keep their
    password and profile, but get the role listed here.
    """
    with app.app_context():
        db.create_all()
        seeds = [(app.config['ADMIN_USER'], app.config['ADMIN_UID'], 'Admin',
                  app.config['ADMIN_PASSWORD'], app.config['ADMIN_EMAIL'])]
        for name, uid, role in app.config['MEMBERS']:
            password = os.environ.get(name.split()[0].upper() + '_PASSWORD') or app.config['DEFAULT_PASSWORD']
            seeds.append((name, uid, role, password, None))

        for name, uid, role, password, email in seeds:
            user = User.query.filter_by(_uid=uid).first()
            if user is None:
                User(name=name, uid=uid, email=email, password=password, role=role).create()
            elif user.role != role:
                user._role = role
                db.session.commit()
