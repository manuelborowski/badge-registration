from flask import render_template
from . import register
from app import flask_app
from flask_login import login_required
from app.application import registration as mregistration
import json


@register.route('/register/<location_key>', methods=['GET'])
def show(location_key):
    return render_template('register/register.html', api_key=flask_app.config['API_KEY'], location_key=location_key)


@register.route('/registration/new/<string:location_key>/<string:badge_code>', methods=['GET'])
def registration_new(location_key, badge_code):
    ret = mregistration.registration_add(badge_code, location_key)
    return(json.dumps(ret))



