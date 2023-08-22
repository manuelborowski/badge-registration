from flask import Blueprint

overview = Blueprint('overview', __name__)

from . import views
