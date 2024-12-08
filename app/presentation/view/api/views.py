from flask import request, send_file
from . import api
from app.application import user as muser, settings as msettings, registration as mregistration
from app.application import socketio as msocketio, location as mlocation, update as mupdate, balance as mbalance, student as mstudent
from app import log, version
import json, sys, html, datetime
from functools import wraps


def api_core(api_level, func, *args, **kwargs):
    try:
        all_keys = msettings.get_configuration_setting('api-keys')
        header_key = request.headers.get('x-api-key')
        if request.headers.get("X-Forwarded-For"):
            remote_ip = request.headers.get("X-Forwarded-For")
        else:
            remote_ip = request.remote_addr
        for i, keys_per_level in  enumerate(all_keys[(api_level - 1)::]):
            if header_key in keys_per_level:
                key_level = api_level + i
                log.info(f"API access by '{keys_per_level[header_key]}', keylevel {key_level}, from {remote_ip}, URI {request.url}")
                try:
                    kwargs["remote_ip"] = remote_ip
                    return func(*args, **kwargs)
                except Exception as e:
                    log.error(f'{func.__name__}: {e}')
                    return json.dumps({"status": False, "data": f'API-EXCEPTION {func.__name__}: {html.escape(str(e))}'})
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return json.dumps({"status": False, "data": html.escape(str(e))})
    log.error(f"API, API key not valid, {header_key}, from {remote_ip} , URI {request.url}")
    return json.dumps({"status": False, "data": f'API key not valid'})


def user_key_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return api_core(muser.UserLevel.USER, func, *args, **kwargs)
        return wrapper


def supervisor_key_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return api_core(muser.UserLevel.SUPERVISOR, func, *args, **kwargs)
        return wrapper


def admin_key_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return api_core(muser.UserLevel.ADMIN, func, *args, **kwargs)
        return wrapper


@api.route('/api/user/add', methods=['POST'])
@admin_key_required
def user_add(**kwargs):
    data = json.loads(request.data)
    ret = muser.api_user_add(data)
    return(json.dumps(ret))


@api.route('/api/user/update', methods=['POST'])
@admin_key_required
def user_update(**kwargs):
    data = json.loads(request.data)
    ret = muser.api_user_update(data)
    return(json.dumps(ret))


@api.route('/api/user/delete', methods=['POST'])
@admin_key_required
def user_delete(**kwargs):
    data = json.loads(request.data)
    ret = muser.api_user_delete(data)
    return(json.dumps(ret))


@api.route('/api/user/get', methods=['GET'])
@admin_key_required
def user_get(**kwargs):
    options = request.args
    ret = muser.api_user_get(options)
    return(json.dumps(ret))


@api.route('/api/schoolrekening/get', methods=['GET'])
@user_key_required
def schoolrekening_get(**kwargs):
    options = request.args
    ret = mregistration.api_schoolrekening_get(options)
    return(json.dumps(ret))


@api.route('/api/schoolrekening/artikels', methods=['GET'])
@user_key_required
def schoolrekening_artikels_get(**kwargs):
    ret = mregistration.api_schoolrekening_artikels_get()
    return(json.dumps(ret))


@api.route('/api/schoolrekening/info', methods=['GET'])
def schoolrekening_info(**kwargs):
    ret = mregistration.api_schoolrekening_info()
    return ret


@api.route('/api/registration/add', methods=['POST'])
@user_key_required
def registration_add(*args, **kwargs):
    client_ip = kwargs['remote_ip'] if 'remote_ip' in kwargs else None
    data = json.loads(request.data)
    code = data["badge_code"] if "badge_code" in data else None
    leerlingnummer = data["leerlingnummer"] if "leerlingnummer" in data else None
    location = data["location_key"]
    timestamp = data["timestamp"] if "timestamp" in data else None
    ret = mregistration.registration_add(location, timestamp, leerlingnummer, code)

    for item in ret:
        if item["to"] == "ip" and client_ip:
            msocketio.send_to_room(item, client_ip)
        elif item["to"] == "location":
            msocketio.send_to_room(item, location)
        elif item["to"] == "broadcast":
            msocketio.broadcast_message(item)
        else:
            log.error(f'{sys._getframe().f_code.co_name}: No valid "to" parameter: {item["to"]}')
            return json.dumps({"status": False, "data": f'No valid "to" parameter: {item["to"]}'})
    return json.dumps({"status": True})


@api.route('/api/registration/update', methods=['POST'])
@user_key_required
def registration_update(**kwargs):
    data = json.loads(request.data)
    ids = data["ids"]
    location = data["location_key"]
    fields = data["fields"]
    ret = mregistration.api_registration_update(location, ids, fields)
    msocketio.send_to_room({'type': 'update-items-in-list-of-registrations', 'data': ret}, location)
    return json.dumps({"status": ret["status"]})


@api.route('/api/registration/message', methods=['POST'])
@user_key_required
def registration_send_message(**kwargs):
    data = json.loads(request.data)
    ids = data["ids"]
    location = data["location_key"]
    ret = mregistration.api_registration_send_message(ids, location)
    msocketio.send_to_room({'type': 'update-items-in-list-of-registrations', 'data': ret}, location)
    return json.dumps({"status": ret["status"]})


@api.route('/api/registration/delete', methods=['POST'])
@supervisor_key_required
def registration_delete(**kwargs):
    data = json.loads(request.data)
    ids = data["ids"]
    location = data["location"]
    ret = mregistration.api_registration_delete(ids)
    msocketio.send_to_room({'type': 'update-list-of-registrations', 'data': ret}, location)
    return json.dumps(ret)


@api.route('/api/reservation/add', methods=['POST'])
@supervisor_key_required
def add_reservation(**kwargs):
    data = json.loads(request.data)
    leerlingnummer = data["leerlingnummer"]
    location = data["location_key"]
    item = data["item"]
    ret = mstudent.api_reservation_add(leerlingnummer, location, item)
    return json.dumps({"status": ret["status"]})


@api.route('/api/location/get', methods=['GET'])
@user_key_required
def locations_get(**kwargs):
    ret = mlocation.get_locations()
    return(json.dumps(ret))


@api.route('/api/location_article/get', methods=['GET'])
@user_key_required
def locations_articles_get(**kwargs):
    ret = mlocation.get_locations_articles()
    return(json.dumps(ret))


#get the software version
@api.route('/api/version/get', methods=['GET'])
@user_key_required
def version_get_server(**kwargs):
    ret = {"version": version}
    return(json.dumps(ret))


# to prevent syncing twice the same registrations:
# find oldest registration in list
# from database, get all registrations, later than oldest
# matching registrations are skipped
@api.route('/api/sync/registrations/data', methods=['POST'])
@supervisor_key_required
def sync_registrations_data(**kwargs):
    data = json.loads(request.data)
    nbr_new, nbr_doubles = mregistration.sync_registrations_server(data["data"])
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_doubles": nbr_doubles}}
    return json.dumps(ret)


#client side api:
# get software version from server and compare with own version
# get, from server, all missing sql-scripts and update script
# run, in sequence, all sql scripts and run update script.
@api.route('/api/update/client', methods=['POST'])
@user_key_required
def update_software_client(**kwargs):
    data = json.loads(request.data)
    nbr_new, nbr_doubles = mregistration.sync_registrations_server(data["data"])
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_doubles": nbr_doubles}}
    return json.dumps(ret)


# serverside api
@api.route('/api/update/server', methods=['GET'])
@user_key_required
def update_software_server(**kwargs):
    versions = request.args.get("versions", "")
    ret = mupdate.get_update_data(versions)
    return ret


@api.route('/api/update/version', methods=['GET'])
@user_key_required
def get_update_version(**kwargs):
    ret = mupdate.get_latest_update_version()
    return ret

@api.route('/api/papercut/upload', methods=['POST'])
@user_key_required
def papercut_upload(**kwargs):
    files = [f for f in request.files.getlist("papercut_file")]
    ret = mbalance.papercut_upload(files)
    return ret

@api.route('/api/my_ip', methods=['GET'])
@user_key_required
def get_my_ip(**kwargs):
    ret = {"ipaddress":  kwargs["remote_ip"] if "remote_ip" in kwargs else ""}
    return json.dumps(ret)

hb_timestamp = int(datetime.datetime.now().timestamp())
@api.route('/api/hb', methods=['GET'])
def hb():
    ret = {"hb": hb_timestamp}
    return json.dumps(ret)




