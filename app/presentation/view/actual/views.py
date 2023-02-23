from . import actual
from app import log
from flask import redirect, url_for, request, render_template
from flask_login import login_required, current_user
from app.data.datatables import DatatableConfig
from app.presentation.view import datatables
from app.application import socketio as msocketio, settings as msettings, cardpresso as mcardpresso, location as mlocation, registration as mregistration

import sys
import app.data
import app.application.student
from app.application.settings import get_configuration_setting


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
    locations = mlocation.get_locations()
    location_choices = [[l["key"], l["locatie"]] for l in locations]
    return [
        {
            'type': 'select',
            'name': 'filter-location',
            'label': 'Locaties',
            'choices': location_choices,
            'default': location_choices[0][0],
        },
    ]