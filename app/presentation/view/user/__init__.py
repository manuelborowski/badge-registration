# -*- coding: utf-8 -*-
# flapp/auth/__init__.py

from flask import Blueprint

user = Blueprint('user', __name__)

from . import views
