import datetime, sys, base64, requests
import app.application
import app.application.api
import app
from app import log, flask_app
from app.data import student as mstudent, registration as mregistration, utils as mutils, photo as mphoto, settings as msettings
from app.application.util import get_api_key
from flask_login import current_user

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def registration_add(rfid, location_key, timestamp=None):
    try:
        if timestamp:
            now = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        else:
            now = datetime.datetime.now()
        today = now.date()
        student = mstudent.student_get([("rfid", "=", rfid)])
        if student:
            photo_obj = mphoto.photo_get({"id": student.foto_id})
            photo = base64.b64encode(photo_obj.photo).decode('utf-8') if photo_obj else ''
            location_settings = msettings.get_configuration_setting("location-profiles")
            if location_key not in location_settings:
                log.info(f'{sys._getframe().f_code.co_name}:  {location_key} is not valid')
                return {"status": False, "data": f"Locatie {location_key} is niet geldig"}
            location = location_settings[location_key]
            ret = {
                "status": True,
                "selected_day": str(today),
                "action": "delete",
                "data": [{
                    "leerlingnummer": student.leerlingnummer,
                    "naam": student.naam,
                    "voornaam": student.voornaam,
                    "photo": photo,
                    "klascode": student.klascode,
                }]
            }
            if location["type"] == "nietverplicht":
                registrations = mregistration.registration_get_m([("leerlingnummer", "=", student.leerlingnummer), ("location", "=", location_key), ("time_in", ">", today)], order_by="id")
                if registrations:
                    last_registration = registrations[-1]
                    if last_registration.time_out is None:
                        mregistration.registration_update(last_registration, {"time_out": now})
                        log.info(f'{sys._getframe().f_code.co_name}: Badge out, {student.leerlingnummer} at {now}')
                        ret["data"][0].update({"timestamp": str(last_registration.time_in), "id": last_registration.id,})
                        return ret
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: Badge in, {student.leerlingnummer} at {now}')
                    ret.update({"action": "add"})
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id,})
                    return ret
            if location["type"] == "verkoop":
                artikel = msettings.get_configuration_setting("artikel-profiles")[location["artikel"]]
                nbr_items = 1
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now,
                                                               "prijs_per_item": artikel["prijs-per-item"], "aantal_items": nbr_items})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: Verkoop({location["locatie"]}), {student.leerlingnummer} at {now}, price-per-item {artikel["prijs-per-item"]}, nbr items {nbr_items}')
                    ret.update({"action": "add"})
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id,})
                    return ret
            log.info(f'{sys._getframe().f_code.co_name}:  {student.leerlingnummer} could not make a registration')
            return {"status": False, "data": "Kan geen nieuwe registratie maken"}
        log.info(f'{sys._getframe().f_code.co_name}:  {rfid} not found in database')
        return {"status": False, "data": f"Kan student met rfid {rfid} niet vinden in database"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f"Fout, {str(e)}"}


def get_current_registrations(location, selected_day=None):
    try:
        if not selected_day:
            selected_day = str(datetime.datetime.now())
        time_in_low = datetime.datetime.strptime(selected_day, "%Y-%m-%d").date()
        time_in_high = time_in_low + datetime.timedelta(days=1)
        registrations = mregistration.registration_get_m([("location", "=", location), ("time_in", ">", time_in_low), ("time_in", "<", time_in_high), ("time_out", "=", None)], order_by="id")
        data = []
        ret = {'status': True, "action": "add", "data": data, "selected_day": selected_day}
        for registration in registrations:
            student = mstudent.student_get([("leerlingnummer", "=", registration.leerlingnummer)])
            photo = mphoto.photo_get({"id": student.foto_id})
            data.append({
                "leerlingnummer": student.leerlingnummer,
                "naam": student.naam,
                "voornaam": student.voornaam,
                "klascode": student.klascode,
                "photo": base64.b64encode(photo.photo).decode('utf-8') if photo and photo.photo else '',
                "timestamp": str(registration.time_in),
                "id": registration.id
            })
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {'status': False, 'message': str(e)}


def clear_all_registrations(location):
    try:
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0)
        registrations = mregistration.registration_get_m([("location", "=", location), ("time_in", ">", today), ("time_out", "=", None)], order_by="id")
        clear_registrations = [{"item": r, "time_out": now} for r in registrations]
        mregistration.registration_update_m(clear_registrations)
        return True
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return False


def api_schoolrekening_get(options):
    try:
        _, filters, _, _ = app.application.api.api_process_options(options)
        artikel = [v for k, o, v in filters if k == "artikel"][0]
        filters = [(k, o, v) for k, o, v in filters if k != "artikel"]
        locations = msettings.get_configuration_setting("location-profiles")
        artikel_profiel = msettings.get_configuration_setting("artikel-profiles")[artikel]
        location_keys = [k for k,v in locations.items() if v["type"] == "verkoop" and v["artikel"] == artikel]
        data_out = []
        leerlingnummers = {}
        for key in location_keys:
            filters.append(("location", "=", key))
            registrations = mregistration.registration_get_m(filters)
            for item in registrations:
                if item.leerlingnummer in leerlingnummers:
                    leerlingnummers[item.leerlingnummer] += 1
                else:
                    leerlingnummers[item.leerlingnummer] = 1
            filters = filters[:-1]
        info = artikel_profiel["info"]
        prijs_per_item = artikel_profiel["prijs-per-item"]
        for leerlingnummer, nbr in leerlingnummers.items():
            data_out.append({"leerlingnummer": leerlingnummer, "info": info.replace("$aantal$", str(nbr)), "bedrag": prijs_per_item * nbr / 100})
        return {"status": True, "data": data_out}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_registration_add(code, location_key, timestamp):
    try:
        ret = app.application.registration.registration_add(code, location_key, timestamp)
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_registration_delete(ids):
    try:
        mregistration.registration_delete_m(ids)
        return {"status": True, "data": ""}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_schoolrekening_artikels_get():
    try:
        artikels = msettings.get_configuration_setting("artikel-profiles")
        return {"status": True, "data": [k for k, _ in artikels.items()]}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_schoolrekening_info():
    info_page = msettings.get_configuration_setting("api-schoolrekening-info")
    return info_page


def sync_registrations(data):
    try:
        nbr_doubles = 0
        new_registrations = []
        if data:
            registrations = []
            for d in data:
                try:
                    r0 = datetime.datetime.strptime(d[0], "%Y-%m-%d %H:%M:%S")
                except:
                    r0 = None
                try:
                    r1 = datetime.datetime.strptime(d[1], "%Y-%m-%d %H:%M:%S")
                except:
                    r1 = None
                registrations.append([r0, r1, d[2], d[3]])
            registrations = sorted(registrations, key=lambda x: x[0])
            oldest = registrations[0]
            log.info(f"Oldest, {oldest}")
            db_registrations = mregistration.registration_get_m([("time_in", ">=", oldest[0])])
            db_cache = {str(d.time_in) + d.leerlingnummer + d.location: d for d in db_registrations}
            for registration in registrations:
                key = str(registration[0]) + registration[2] + registration[3]
                if key in db_cache:
                    log.info(f'{sys._getframe().f_code.co_name}: registration already present, {registration}')
                    nbr_doubles += 1
                    continue
                new_registrations.append({"leerlingnummer": registration[2], "location": registration[3], "time_in": registration[0], "time_out": registration[1]})
                log.info(f"New registration, {registration}")
            mregistration.registration_add_m(new_registrations)
        return len(new_registrations), nbr_doubles
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return 0, 0


#get registrations from database and send to remote server
def sync_registrations_start():
    try:
        registrations = mregistration.registration_get_m()
        data = [[str(r.time_in), str(r.time_out), r.leerlingnummer, r.location] for r in registrations]
        api_key = get_api_key(current_user.level)
        ret = requests.post(f"{flask_app.config['SYNC_REGISTRATIONS_URL']}/api/sync/registrations/data", headers={'x-api-key': api_key}, json={"data": data})
        if ret.status_code == 200:
            res = ret.json()
            if res["status"]:
                mregistration.registration_delete_m(registrations=registrations)
                return res["data"]["nbr_new"], res["data"]["nbr_doubles"]
        return 0, 0
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return 0, 0
