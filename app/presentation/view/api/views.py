from flask import request
from . import api
from app.application import user as muser, settings as msettings, registration as mregistration, socketio as msocketio, location as mlocation
from app.application.student import student_load_from_sdh
from app import log
import json, sys, html
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
def user_add():
    data = json.loads(request.data)
    ret = muser.api_user_add(data)
    return(json.dumps(ret))


@api.route('/api/user/update', methods=['POST'])
@admin_key_required
def user_update():
    data = json.loads(request.data)
    ret = muser.api_user_update(data)
    return(json.dumps(ret))


@api.route('/api/user/delete', methods=['POST'])
@admin_key_required
def user_delete():
    data = json.loads(request.data)
    ret = muser.api_user_delete(data)
    return(json.dumps(ret))


@api.route('/api/user/get', methods=['GET'])
@admin_key_required
def user_get():
    options = request.args
    ret = muser.api_user_get(options)
    return(json.dumps(ret))


@api.route('/api/schoolrekening/get', methods=['GET'])
@user_key_required
def schoolrekening_get():
    options = request.args
    ret = mregistration.api_schoolrekening_get(options)
    return(json.dumps(ret))


@api.route('/api/schoolrekening/artikels', methods=['GET'])
@user_key_required
def schoolrekening_artikels_get():
    ret = mregistration.api_schoolrekening_artikels_get()
    return(json.dumps(ret))


@api.route('/api/schoolrekening/info', methods=['GET'])
def schoolrekening_info():
    ret = mregistration.api_schoolrekening_info()
    return ret


@api.route('/api/registration/add', methods=['POST'])
@user_key_required
def registration_add():
    data = json.loads(request.data)
    code = data["badge_code"]
    location = data["location_key"]
    timestamp = data["timestamp"] if "timestamp" in data else None
    ret = mregistration.api_registration_add(code, location, timestamp)
    msocketio.send_to_room({'type': 'update-current-status', 'data': ret}, location)
    return json.dumps({"status": ret["status"]})


@api.route('/api/registration/delete', methods=['POST'])
@supervisor_key_required
def registration_delete():
    ids = json.loads(request.data)
    ret = mregistration.api_registration_delete(ids)
    return json.dumps(ret)


@api.route('/api/location/get', methods=['GET'])
@user_key_required
def locations_get():
    ret = mlocation.get_locations()
    return(json.dumps(ret))


@api.route('/api/sync/students/start', methods=['POST'])
@supervisor_key_required
def sync_students_start():
    # return json.dumps({"status": True, "data": {"nbr_new": 0, "nbr_updated": 0, "nbr_deleted": 0}})
    nbr_new, nbr_updated, nbr_deleted = student_load_from_sdh()
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_updated": nbr_updated, "nbr_deleted": nbr_deleted }}
    return json.dumps(ret)


@api.route('/api/sync/registrations/start', methods=['POST'])
@supervisor_key_required
def sync_registrations_start():
    nbr_new, nbr_doubles = mregistration.sync_registrations_start()
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_doubles": nbr_doubles}}
    return json.dumps(ret)


# to prevent syncing twice the same registrations:
# find oldest registration in list
# from database, get all registrations, later than oldest
# matching registrations are skipped
@api.route('/api/sync/registrations/data', methods=['POST'])
@supervisor_key_required
def sync_registrations_data():
    data = json.loads(request.data)
    nbr_new, nbr_doubles = mregistration.sync_registrations(data["data"])
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_doubles": nbr_doubles}}
    return json.dumps(ret)


