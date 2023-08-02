from flask import render_template
from . import register
from app import flask_app
from flask_login import login_required
from app.application import registration as mregistration, socketio as msocketio
import json


@register.route('/register/<location_key>', methods=['GET'])
def show(location_key):
    return render_template('register/register.html', location_key=location_key)


@register.route('/registration/new/<string:location_key>/<string:badge_code>', methods=['GET'])
@register.route('/registration/new/<string:location_key>/<string:badge_code>/<string:timestamp>', methods=['GET'])
def registration_new(location_key, badge_code, timestamp=None):
    ret = mregistration.registration_add(badge_code, location_key, timestamp)
    if ret["status"]:
        actual_status_data = {
            "status": True,
            "action": "add" if ret["data"]["direction"] == "in" else "delete",
            "data": [{
                "leerlingnummer": ret["data"]["student"].leerlingnummer,
                "naam": ret["data"]["student"].naam,
                "voornaam": ret["data"]["student"].voornaam,
                "photo": ret["data"]["photo"],
                "klascode": ret["data"]["student"].klascode,
                "popup_delay": ret["data"]["popup_delay"],
                "timestamp": str(ret["data"]["registration"].time_in),
                "id": ret["data"]["registration"].id,
            }]
        }
    else:
        actual_status_data = {"status": False, "data": ret["data"]}
    msocketio.send_to_room({'type': 'update-current-status', 'data': actual_status_data}, location_key)
    return(json.dumps(actual_status_data))



