from flask import Blueprint

cardpresso = Blueprint('cardpresso', __name__)

from . import views
