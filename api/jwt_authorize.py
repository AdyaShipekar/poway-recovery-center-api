""" JWT cookie guard for API endpoints (same role as Open Coding Society flask api/jwt_authorize.py) """
from functools import wraps

import jwt
from flask import request, current_app, g

from model.user import User


def token_required(roles=None):
    '''
    Guards API endpoints with the JWT stored in the request cookie.
    Sets g.current_user for the decorated function.
      401 / Unauthorized: token missing, invalid, expired, or user no longer exists
      403 / Forbidden: user does not have one of the required roles
    '''
    if isinstance(roles, str):
        roles = [roles]

    def decorator(func_to_guard):
        @wraps(func_to_guard)
        def decorated(*args, **kwargs):
            token = request.cookies.get(current_app.config["JWT_TOKEN_NAME"])
            if not token:
                return {"message": "Authentication Token is missing!", "data": None, "error": "Unauthorized"}, 401
            try:
                data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            except jwt.PyJWTError:
                return {"message": "Your session has expired. Please log in again.", "data": None, "error": "Unauthorized"}, 401

            user = User.query.filter_by(_uid=data.get("_uid")).first()
            if user is None or data.get("token_version") != user.token_version:
                return {"message": "Invalid Authentication token!", "data": None, "error": "Unauthorized"}, 401
            if roles and user.role not in roles:
                return {"message": "Insufficient permissions.", "data": None, "error": "Forbidden"}, 403

            g.current_user = user
            return func_to_guard(*args, **kwargs)
        return decorated
    return decorator
