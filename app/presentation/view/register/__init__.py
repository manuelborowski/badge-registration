from flask import Blueprint

register = Blueprint('register', __name__)

from . import views

