from flask import Blueprint

warning = Blueprint('warning', __name__)

from . import views
