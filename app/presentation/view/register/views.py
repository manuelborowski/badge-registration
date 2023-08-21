from flask import render_template, request
from . import register
from app import flask_app
from app.application import registration as mregistration, socketio as msocketio, settings as msettings
import json


@register.route('/register/<location_key>', methods=['GET'])
def show(location_key):
    api_keys = msettings.get_configuration_setting('api-keys')[0]
    api_key = [k for k, v in api_keys.items() if v == "local"][0]
    return render_template('register/register.html', location_key=location_key, api_key=api_key)



