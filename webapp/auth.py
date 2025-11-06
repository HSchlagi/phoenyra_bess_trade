"""
Authentication utilities for BESS Trading Dashboard
"""
from functools import wraps
from flask import session, redirect, url_for, request, abort

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    """Decorator to require specific role(s) for a route"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get('user')
            if not user or user.get('role') not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

