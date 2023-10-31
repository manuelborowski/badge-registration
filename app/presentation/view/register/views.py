from flask import render_template, request
from . import register
from flask_login import login_required
from app.application import registration as mregistration, settings as msettings, location as mlocation
import json


@register.route('/register/<location_key>', methods=['GET'])
def show(location_key):
    api_keys = msettings.get_configuration_setting('api-keys')[0]
    api_key = [k for k, v in api_keys.items() if v == "local"][0]
    location = msettings.get_configuration_setting("location-profiles")[location_key]
    location.update({"key": location_key})
    return render_template('register/register.html', location=location, api_key=api_key)


@register.route('/register/sync', methods=['POST'])
@login_required
def sync_registrations():
    nbr_new, nbr_doubles = mregistration.sync_registrations_client()
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_doubles": nbr_doubles}}
    return json.dumps(ret)


@register.route('/location_article/sync', methods=['GET'])
@login_required
def sync_locations_articles():
    nbr_locations, nbr_articles = mlocation.sync_locations_articles_client()
    ret = {"status": True, "data": {"nbr_locations": nbr_locations, "nbr_articles": nbr_articles}}
    return json.dumps(ret)



