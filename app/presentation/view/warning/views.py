from . import warning  
from app import supervisor_required, log
from flask import redirect, url_for
from flask_login import login_required
from app.presentation.view import datatables
from app.data.models import Warning
from app.data import warning as mwarning
from app.application import socketio as msocketio, warning as amwarning
import json, sys


@warning.route('/warning', methods=['POST', 'GET'])
@login_required
@supervisor_required
def show():
    return datatables.show(table_configuration)


@warning.route('/warning/table_ajax', methods=['GET', 'POST'])
@login_required
@supervisor_required
def table_ajax():
    return datatables.ajax(table_configuration)


@warning.route('/warning/table_action', methods=['GET', 'POST'])
@login_required
@supervisor_required
def table_action():
    return redirect(url_for('warning.show'))


# propagate changes in (some) properties to the table
def warning_update_cb(value, opaque):
    msocketio.broadcast_message({'type': 'celledit-warning', 'data': {'reload-table': True}})

amwarning.subscribe_updated(warning_update_cb, None)


# some columns can be edit inplace in the table.
def celledit_event_cb(msg, client_sid=None):
    try:
        nbr = msg['data']['column']
        column_template = table_configuration['template'][nbr]
        if 'celltoggle' in column_template or 'celledit' in column_template:
            amwarning.update_warning(msg['data']['id'], {column_template['data']: msg['data']['value']})
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    msocketio.send_to_room({'type': 'celledit-registration', 'data': {'status': True}}, client_sid)

msocketio.subscribe_on_type('celledit-warning', celledit_event_cb)


def get_filters():
    choices = [['default', 'Alles'], ['True', 'Zichtbaar']]
    return [
        {
            'type': 'select',
            'name': 'visible',
            'label': 'Zichtbaar?',
            'choices': choices,
            'default': 'default',
        },
    ]


table_configuration = {
    'view': 'warning',
    'title': 'Waarschuwingen',
    'buttons': [],
    'template': [
        {'name': 'row_action', 'data': 'row_action', 'width': '1%', 'visible': 'never'},
        {'name': 'Tijd', 'data': 'timestamp_dutch', 'order_by': Warning.timestamp, 'orderable': True, 'width': '10%', 'visible': 'yes'},
        {'name': 'Z', 'data': 'visible', 'order_by': Warning.visible, 'width': '1%', 'celledit': {"type": 'toggle'}, 'visible': 'yes'},
        {'name': 'Waarschuwing', 'data': 'message', 'order_by': Warning.message, 'orderable': True, 'width': '80%', 'visible': 'yes'},
    ],
    'get_filters': get_filters,
    'item': {},
    'href': [],
    'pre_filter': mwarning.pre_filter,
    'filter_data': mwarning.filter_data,
    'format_data': mwarning.format_data,
    'search_data': mwarning.search_data,
    'default_order': (1, 'asc'),
    'socketio_endpoint': 'celledit-warning',
}
