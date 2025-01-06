import sys, json

from flask import render_template, request
from flask_login import login_required, current_user

from app import log, flask_app
from app.application import socketio as msocketio, registration as mregistration, settings as msettings, util as mutil
from . import overview
from app.application.settings import get_configuration_setting


@overview.route('/overview/show', methods=['POST', 'GET'])
@login_required
def show():
    popups = {'popup-export-registrations': get_configuration_setting("popup-export-registrations")}
    return render_template('overview/overview.html', title="Overzicht", filters=get_filters(), popups=popups)


def get_current_registrations(msg, client_sid=None):
    try:
        filters = msg["data"]["filters"]
        ret = mregistration.registration_get(filters)
        msocketio.send_to_client({'type': 'update-list-of-registrations', 'data': ret})
    except Exception as e:
        msocketio.send_to_client({'type': 'update-list-of-registrations', 'data': {'status': False, 'message': str(e)}})


def clear_all_registrations(msg, client_sid=None):
    try:
        ret = mregistration.clear_all_registrations(msg["data"]["location"])
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


msocketio.subscribe_on_type('request-list-of-registrations', get_current_registrations)
msocketio.subscribe_on_type('clear-all-registrations', clear_all_registrations)

@overview.route('/overview/export/<string:key>/<string:startdate>/<string:enddate>', methods=['GET'])
def export_registrations(key, startdate, enddate):
    try:
        ret = mregistration.registration_export(key, startdate, enddate)
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f'{sys._getframe().f_code.co_name}: {e}'}

@overview.route('/overview/reset_counters', methods=['POST', 'GET'])
@login_required
def reset_counters():
    data = json.loads(request.data)
    location = data["location"]
    ret = mregistration.registration_zero_counters(location)
    return json.dumps(ret)

def get_filters():
    try:
        locations = msettings.get_configuration_setting("location-profiles")
        if locations:
            user_level = current_user.level if current_user.is_authenticated else 1
            location_choices = [[k, l["locatie"]] for k, l in locations.items() if "access_level" not in l or l["access_level"] <= user_level]
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
                    'choices': [["on-date", "Op datum"], ["last-week", "Laatste week"], ["last-2-months", "Laatste 2 maanden"], ["last-4-months", "Laatste 4 maandend"]],
                    'default': "last-week",
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
