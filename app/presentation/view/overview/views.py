import sys

from flask import render_template
from flask_login import login_required, current_user

from app import log, flask_app
from app.application import socketio as msocketio, registration as mregistration, settings as msettings, util as mutil
from . import overview


@overview.route('/overview/show', methods=['POST', 'GET'])
@login_required
def show():
    return render_template('overview/overview.html', title="Overzicht", filters=get_filters(["sms", "nietverplicht", "verkoop"]))


def get_current_registrations(msg, client_sid=None):
    location_key = msg["data"]["location"]
    date = msg["data"]["date"]
    try:
        ret = mregistration.get_current_registrations(location_key, date)
        msocketio.send_to_client({'type': 'update-current-status', 'data': ret})
    except Exception as e:
        msocketio.send_to_client({'type': 'update-current-status', 'data': {'status': False, 'message': str(e)}})


def clear_all_registrations(msg, client_sid=None):
    try:
        ret = mregistration.clear_all_registrations(msg["data"]["location"])
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


msocketio.subscribe_on_type('get-current-registrations', get_current_registrations)
msocketio.subscribe_on_type('clear-all-registrations', clear_all_registrations)


def get_filters(location_types):
    try:
        locations = msettings.get_configuration_setting("location-profiles")
        if locations:
            if type(location_types) is not list:
                location_types = [location_types]
            location_choices = [[k, l["locatie"]] for k, l in locations.items() if l["type"] in location_types]
            location_choices.sort(key=lambda x: x[1])
            return [
                {
                    'type': 'select',
                    'name': 'filter-location',
                    'label': 'Locaties',
                    'choices': location_choices,
                    'default': location_choices[0][0],
                },
            ]
        return []
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return []
