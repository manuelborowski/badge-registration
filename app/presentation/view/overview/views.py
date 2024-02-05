import sys

from flask import render_template
from flask_login import login_required, current_user

from app import log, flask_app
from app.application import socketio as msocketio, registration as mregistration, settings as msettings, util as mutil
from . import overview


@overview.route('/overview/show_nietverplicht', methods=['POST', 'GET'])
@login_required
def show_nietverplicht():
    api_key = mutil.get_api_key(current_user.level)
    return render_template('overview/overview.html', title="Registratie, niet verplicht", buttons=["remove-all"], filters=get_filters("nietverplicht"), right_click=get_right_click_settings(), api_key=api_key)


@overview.route('/overview/show_verplicht', methods=['POST', 'GET'])
@login_required
def show_verplicht():
    api_key = mutil.get_api_key(current_user.level)
    return render_template('overview/overview.html', title="Registratie, verplicht", filters=get_filters("sms"), right_click=get_right_click_settings(), api_key=api_key)


@overview.route('/overview/show_verkoop', methods=['POST', 'GET'])
@login_required
def show_verkoop():
    api_key = mutil.get_api_key(current_user.level)
    return render_template('overview/overview.html', title="Verkoop", buttons=[], filters=get_filters("verkoop"), right_click=get_right_click_settings(), api_key=api_key)


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
            if location_types is not type(list):
                location_types = [location_types]
            location_choices = [[k, l["locatie"]] for k, l in locations.items() if l["type"] in location_types]
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

def get_right_click_settings():
    settings = {
        'endpoint': 'student.right_click',
        'menu': [
            {'label': 'Verwijder registratie', 'item': 'delete', 'iconscout': 'trash-alt'},
        ]
    }
    return settings


