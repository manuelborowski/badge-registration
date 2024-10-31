from app import flask_app, login_manager
from app.data.user import load_user as user_load_user

# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    return user_load_user(user_id)


__all__ = ['models', 'settings', 'user', 'utils', 'warning', 'student', 'registration', 'staff', "reservation"]


import app.data.models
import app.data.settings
import app.data.student
import app.data.staff
import app.data.photo
import app.data.warning
import app.data.utils
import app.data.user
import app.data.registration
import app.data.reservation
