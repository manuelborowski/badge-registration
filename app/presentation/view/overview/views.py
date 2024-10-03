import sys

from flask import render_template
from flask_login import login_required, current_user

from app import log, flask_app
from app.application import socketio as msocketio, registration as mregistration, settings as msettings, util as mutil
from . import overview


@overview.route('/overview/show', methods=['POST', 'GET'])
@login_required
def show():
    return render_template('overview/overview.html', title="Overzicht", filters=get_filters(["sms", "cellphone", "nietverplicht", "verkoop"]))


def get_current_registrations(msg, client_sid=None):
    filters = msg["data"]["filters"]
    try:
        ret = mregistration.registration_get(filters)
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
                    "store": True
                },
                {
                    'type': 'select',
                    'name': 'sort-on-select',
                    'label': 'Sorteer op',
                    'choices': [["timestamp", "Tijdstempel"], ["name-firstname", "Naam, voornaam"], ["klas-name-firstname", "Klas, naam, voornaam"]],
                    'default': "timestamp",
                    "store": True
                },
                {
                    'type': 'date',
                    'name': 'filter-date',
                    'label': 'Datum',
                    'default': "today",
                    "store": True
                },
                {
                    'type': 'text',
                    'name': 'search-text',
                    'label': 'Zoeken',
                    "store": False,
                },
                {
                    'type': 'select',
                    'name': 'view-layout-select',
                    'label': 'Layout',
                    'choices': [["tile", "Tegel"], ["list", "Lijst"]],
                    'default': "list",
                    "store": True
                },
                {
                    'type': 'select',
                    'name': 'photo-size-select',
                    'label': 'Foto grootte',
                    'choices': [["50", "50%"], ["75", "75%"], ["100", "100%"], ["150", "150%"], ],
                    'default': "50",
                    "store": True
                },
                {
                    'type': 'select',
                    'name': 'period-select',
                    'label': 'Periode',
                    'choices': [["on-date", "Op datum"], ["last-2-months", "Laatste 2 maanden"], ["last-4-months", "Laatste 4 maandend"]],
                    'default': "on-date",
                    "store": True
                },
                {
                    'type': 'select',
                    'name': 'sms-specific-select',
                    'label': 'Filter op',
                    'choices': [["all", "Alles"], ["no-sms-sent", "Geen sms gestuurd"], ["no-ack", "Niet bevestigd"]],
                    'default': "all",
                    "extra": True
                },
                {
                    'type': 'select',
                    'name': 'cellphone-specific-select',
                    'label': 'Filter op',
                    'choices': [["all", "Alles"], ["no-message-sent", "Geen bericht gestuurd"]],
                    'default': "all",
                    "extra": True
                },
            ]
        return []
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return []
