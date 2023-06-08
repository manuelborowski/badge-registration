import sys

from flask import render_template
from flask_login import login_required

from app import log
from app.application import socketio as msocketio, location as mlocation, registration as mregistration
from . import actual


@actual.route('/actual/show', methods=['POST', 'GET'])
@login_required
def show():
    return render_template('actual/actual.html', filters=get_filters())


def get_all_actual_registrations(msg, client_sid=None):
    try:
        ret = mregistration.get_all_actual_registrations(msg["data"]["location"])
        msocketio.send_to_client({'type': 'update-actual-status', 'data': {'status': True, "action": "add", "data": ret}})
    except Exception as e:
        msocketio.send_to_client({'type': 'settings', 'data': {'status': False, 'message': str(e)}})


def clear_all_registrations(msg, client_sid=None):
    try:
        ret = mregistration.clear_all_registrations(msg["data"]["location"])
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


msocketio.subscribe_on_type('get-all-actual-registrations', get_all_actual_registrations)
msocketio.subscribe_on_type('clear-all-registrations', clear_all_registrations)


def get_filters():
    try:
        locations = mlocation.get_locations()
        if locations:
            location_choices = [[k, l["locatie"]] for k, l in locations.items()]
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