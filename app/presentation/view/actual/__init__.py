from flask import Blueprint

actual = Blueprint('actual', __name__)

from . import views
