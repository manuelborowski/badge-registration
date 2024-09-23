import datetime, sys, base64, requests
import app.application
import app.application.api
import app
from app import flask_app
from app.data import student as mstudent, registration as mregistration, photo as mphoto, settings as msettings
from app.application.util import get_api_key
from flask_login import current_user
from app.application.sms import send_sms

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def registration_add(location_key, timestamp=None, leerlingnummer=None, rfid=None):
    try:
        if timestamp:
            now = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        else:
            now = datetime.datetime.now()
        now = now.replace(microsecond=0)
        today = now.date()
        if rfid:
            student = mstudent.student_get([("rfid", "=", rfid)])
        elif leerlingnummer:
            student = mstudent.student_get([("leerlingnummer", "=", leerlingnummer)])
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
                "date": str(today),
                "action": "add",
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
                        return {"status": True, "action": "delete", "data": [{"id": last_registration.id}]}
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: Badge in, {student.leerlingnummer} at {now}')
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id,})
                    return ret

            if location["type"] == "verkoop":
                artikel = msettings.get_configuration_setting("artikel-profiles")[location["artikel"]]
                nbr_items = 1
                if "dagmasker" in location:
                    mask = getattr(student, location["dagmasker"])
                    if mask == "":
                        log.info(f'{sys._getframe().f_code.co_name}:  {student.leerlingnummer}, cannot have this artikel')
                        return {"status": False, "data": f"Student {student.naam} {student.voornaam} is niet ingeschreven voor dit artikel"}
                    day_index = datetime.datetime.now().weekday()
                    max_qty = int(mask[day_index])
                    current_qty = int(mask[day_index+6])
                    if current_qty >= max_qty:
                        log.info(f'{sys._getframe().f_code.co_name}:  {student.leerlingnummer}, dagmasker, exceeded quantity {current_qty}/{max_qty} ')
                        return {"status": False, "data": f"Student {student.naam} {student.voornaam} heeft het maximum aantal van {max_qty} artikel(s) bereikt"}
                    current_qty += 1
                    mask = mask[:day_index+6] + str(current_qty) + mask[day_index+7:]
                    mstudent.student_update(student, {location["dagmasker"]: mask})
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now,
                                                               "prijs_per_item": artikel["prijs-per-item"], "aantal_items": nbr_items})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: Verkoop({location["locatie"]}), {student.leerlingnummer} at {now}, price-per-item {artikel["prijs-per-item"]}, nbr items {nbr_items}')
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id})
                    return ret

            # When a student is too late in, scan its badge.  An sms is send to the parents and a why-too-late reason needs to be added
            # If the student returns with a valid proof of being late, tick the registration as being acknowledged/finished
            if location["type"] == "sms":
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: SMS ({location["locatie"]}), {student.leerlingnummer} at {now}')
                    text_body = msettings.get_configuration_setting("sms-student-too-late")
                    text_body = text_body.replace("%%VOORNAAM%%", student.voornaam)
                    text_body = text_body.replace("%%NAAM%%", student.naam)
                    text_body = text_body.replace("%%TIJD%%", str(now))
                    enable_send_sms = location["enable_sending"]
                    sms_sent = False
                    if "auto" in location and location["auto"]: # send sms when badge is scanned
                        if "to" in location: # overwrite sms receivers
                            send_sms(location["to"], text_body, enable_send_sms)
                        else:
                            if student.lpv1_gsm != "":
                                send_sms(student.lpv1_gsm, text_body, enable_send_sms)
                            if student.lpv2_gsm != "":
                                send_sms(student.lpv2_gsm, text_body, enable_send_sms)
                        sms_sent = True
                    # text1: remark
                    # flag1: remark is acknowledged
                    # flag2: sms is sent
                    mregistration.registration_update(registration, {"flag2": sms_sent})
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id, "remark": "", "remark_ack": False, "sms_sent": sms_sent})
                    return ret
            # When a student needs to hand in its cellphone, scan its badge.  After 4 scans (to be configurable), the student is highlighted and
            # has to stay over after school
            # aantal_items: store the sequence-counter
            # flag1: cellphone limit reached
            if location["type"] == "cellphone":
                cellphone_limit = location["limiet"]
                last_registration = mregistration.registration_get([("leerlingnummer", "=", student.leerlingnummer), ("location", "=", location_key)], order_by="-id")
                if last_registration:
                    sequence_counter = (last_registration.aantal_items + 1) % cellphone_limit
                else:
                    sequence_counter = 0
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now,
                                                               "aantal_items": sequence_counter, "flag1": sequence_counter == (cellphone_limit - 1)})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: CELLPHONE ({location["locatie"]}), {student.leerlingnummer} at {now}, sequence {sequence_counter}')
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id, "limit_reached": registration.flag1})
                    return ret

            log.info(f'{sys._getframe().f_code.co_name}:  {student.leerlingnummer} could not make a registration')
            return {"status": False, "data": "Kan geen nieuwe registratie maken"}
        log.info(f'{sys._getframe().f_code.co_name}:  rif {rfid}/leerlingnummer {leerlingnummer} not found in database')
        return {"status": False, "data": f"Kan student met rfid {rfid} / leerlingnummer {leerlingnummer} niet vinden in database"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f"Fout, {str(e)}"}


def registration_delete(ids):
    try:
        mregistration.registration_delete_m(ids)
        ret = {
                "status": True,
                "action": "delete",
                "data": [{"id": id} for id in ids]
            }
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f"Fout, {str(e)}"}


def get_current_registrations(location, filter, include_foto):
    try:
        ret_filter = {}
        registrations = []
        locations = msettings.get_configuration_setting("location-profiles")
        if filter["search_text"] != "":
            registrations = mregistration.registration_student_photo_get(location, filter["search_text"], include_foto=include_foto)
            ret_filter = {"search": True}
        elif filter["sms_specific"] == "on_date":
            selected_day = filter["date"]
            if not selected_day:
                selected_day = str(datetime.datetime.now())
            time_in_low = datetime.datetime.strptime(selected_day, "%Y-%m-%d").date()
            time_in_high = time_in_low + datetime.timedelta(days=1)
            registrations = mregistration.registration_student_photo_get(location, None, time_in_low, time_in_high, include_foto=include_foto)
            ret_filter = {"date": selected_day}
        elif filter["sms_specific"] in ["last_2_months", "last_4_months"]:
            delta = 60 if filter["sms_specific"] == "last_2_months" else 120
            time_in_low = datetime.datetime.now() - datetime.timedelta(days=delta)
            registrations = mregistration.registration_student_photo_get(location, None, time_in_low, include_foto=include_foto)
        elif filter["sms_specific"] == "no_sms_sent":
            registrations = mregistration.registration_student_photo_get(location, None, None, None, None, False, include_foto=include_foto)
        elif filter["sms_specific"] == "no_ack":
            registrations = mregistration.registration_student_photo_get(location, None, None, None, False, None, include_foto=include_foto)
        data = []
        ret = {'status': True, "action": "add", "data": data}
        ret.update(ret_filter)
        for tuple in registrations:
            registration = tuple[0]
            student = tuple[1]
            item = {
                "leerlingnummer": student.leerlingnummer,
                "naam": student.naam,
                "voornaam": student.voornaam,
                "klascode": student.klascode,
                "timestamp": str(registration.time_in),
                "id": registration.id
            }
            if include_foto:
                photo = tuple[2]
                item.update({"photo": base64.b64encode(photo.photo).decode('utf-8') if photo and photo.photo else ''})
            if locations[location]["type"] == "sms":
                item.update({
                    "remark": registration.text1,
                    "remark_ack": registration.flag1,
                    "sms_sent": registration.flag2,
                })
            if locations[location]["type"] == "cellphone":
                item.update({"limit_reached": registration.flag1})
            data.append(item)
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


def api_registration_add(location_key, timestamp, leerlingnummer=None, code=None):
    try:
        ret = registration_add(location_key, timestamp, leerlingnummer, code)
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


# use field text1 to store the remark
# use flag1 to store remark ack
# use flag2 to store sms sent
def api_registration_update(id, fields):
    try:
        registration = mregistration.registration_get(("id", "=", id))
        new_fields = {}
        if "remark" in fields: new_fields["text1"] = fields["remark"]
        if "remark_ack" in fields: new_fields["flag1"] = fields["remark_ack"]
        if "sms_sent" in fields: new_fields["flag2"] = fields["sms_sent"]
        mregistration.registration_update(registration, new_fields)
        return {"status": True, "data": {"id": id, "fields": fields}}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_registration_send_sms(id, location_key):
    try:
        registration = mregistration.registration_get(("id", "=", id))
        student = mstudent.student_get([("leerlingnummer", "=", registration.leerlingnummer)])
        if student:
            location_settings = msettings.get_configuration_setting("location-profiles")
            if location_key not in location_settings:
                log.info(f'{sys._getframe().f_code.co_name}:  {location_key} is not valid')
                return {"status": False, "data": f"Locatie {location_key} is niet geldig"}
            location = location_settings[location_key]
            if location["type"] == "sms":
                log.info(f'{sys._getframe().f_code.co_name}: SMS ({location["locatie"]}), {student.leerlingnummer} at {registration.time_in}')
                text_body = msettings.get_configuration_setting("sms-student-too-late")
                text_body = text_body.replace("%%VOORNAAM%%", student.voornaam)
                text_body = text_body.replace("%%NAAM%%", student.naam)
                text_body = text_body.replace("%%TIJD%%", str(registration.time_in))
                enable_send_sms = location["enable_sending"]
                if "to" in location:
                    send_sms(location["to"], text_body, enable_send_sms)
                else:
                    if student.lpv1_gsm != "":
                        send_sms(student.lpv1_gsm, text_body, enable_send_sms)
                    if student.lpv2_gsm != "":
                        send_sms(student.lpv2_gsm, text_body, enable_send_sms)
                mregistration.registration_update(registration, {"flag2": True}) # flag2 is used to indicate sms sent
                return {"status": True, "data": {"id": id, "fields": {"sms_sent": True}}}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_registration_delete(ids):
    try:
        ret = registration_delete(ids)
        return ret
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


# sync registrations from remote (client) into local (server-database).
def sync_registrations_server(data):
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
            mregistration.registration_add_m(new_registrations)
        return len(new_registrations), nbr_doubles
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return 0, 0


#get registrations from local client database and send to remote server
def sync_registrations_client():
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


