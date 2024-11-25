import datetime, sys, base64, requests
import app.application
import app.application.api
import app
from app import flask_app
from app.data import student as mstudent, registration as mregistration, photo as mphoto, settings as msettings, staff as mstaff, reservation as mreservation
from app.application.util import get_api_key
from app.application.smartschool import send_message as ss_send_message
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
        if location_key == "new-rfid":
            reservation_margin = flask_app.config["RESERVATION_MARGIN"]
            minimum_reservation_time = now - datetime.timedelta(seconds=reservation_margin)
            reservations = mreservation.reservation_get_m([("valid", "=", False), ("timestamp", ">", minimum_reservation_time)])
            if reservations:
                reservation = reservations[0]
                if reservation.item == "rfid":
                    rfid = rfid.upper()
                    reservation.data = rfid
                    reservation.valid = True
                    student = mstudent.student_get([("leerlingnummer", "=", reservation.leerlingnummer)])
                    student.rfid = rfid
                    mreservation.commit()
                    log.info(f'{sys._getframe().f_code.co_name}:  Add reservation for {student.leerlingnummer}, {student.naam} {student.voornaam} {location_key}')
                    return {"status": True, "is-reservation": True, "data": f"Student {student.naam} {student.voornaam} heeft nu RFID code {rfid}"}
            log.info(f'{sys._getframe().f_code.co_name}:  No valid reservation for {location_key}')
            return {"status": False, "is-reservation": True, "data": f"Nieuwe RFID niet gelukt.  Misschien te lang gewacht met scannen, probeer nogmaals"}
        location_settings = msettings.get_configuration_setting("location-profiles")
        if location_key not in location_settings:
            log.info(f'{sys._getframe().f_code.co_name}:  {location_key} is not valid')
            return {"status": False, "data": f"Locatie {location_key} is niet geldig"}
        location = location_settings[location_key]
        if "table" in location and location["table"] == "staff":
            staff = mstaff.staff_get(("rfid", "=", rfid))
            log.info(f'{sys._getframe().f_code.co_name}:  Add registration for {staff.code}, {staff.naam} {staff.voornaam} {location_key}')
            ret = {
                "status": True,
                "date": str(today),
                "action": "add",
                "data": [{
                    "leerlingnummer": staff.code,
                    "naam": staff.naam,
                    "voornaam": staff.voornaam,
                    "klascode": staff.code,
                }]
            }
            registration = mregistration.registration_add({"leerlingnummer": staff.code, "location": location_key, "time_in": now})
            if registration:
                ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id})
                return ret

        if rfid:
            student = mstudent.student_get([("rfid", "=", rfid)])
        elif leerlingnummer:
            student = mstudent.student_get([("leerlingnummer", "=", leerlingnummer)])
        else:
            return {"status": False, "data": "Geen RFID of leerlingnummer gevonden"}
        if student:
            photo_obj = mphoto.photo_get({"id": student.foto_id})
            photo = base64.b64encode(photo_obj.photo).decode('utf-8') if photo_obj else ''
            log.info(f'{sys._getframe().f_code.co_name}:  Add registration for {student.leerlingnummer}, {student.naam} {student.voornaam} {location_key}')
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

            # When a student is too late in, scan its badge.  An sms is sent to the parents and a why-too-late reason needs to be added
            # If the student returns with a valid proof of being late, tick the registration as being acknowledged/finished
            # text1: remark
            # flag1: remark is acknowledged
            # flag2: sms is sent
            if location["type"] == "sms":
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now})
                if registration:
                    sms_sent = False
                    if "auto" in location and location["auto"]:  # send sms when badge is scanned
                        sms_sent = __send_sms(registration, location, student)
                    auto_remark = location["auto_remark"] if "auto_remark" in location else False
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id, "remark": "", "remark_ack": False,
                                           "sms_sent": sms_sent, "auto_remark": auto_remark})
                    return ret
            # When a student needs to hand in its cellphone, scan its badge.  After 4 scans (to be configurable), the student is highlighted and
            # has to stay over after school
            # aantal_items: store the sequence-counter
            # flag1: message sent
            if location["type"] == "cellphone":
                last_registration = mregistration.registration_get([("leerlingnummer", "=", student.leerlingnummer), ("location", "=", location_key)], order_by="-id")
                if last_registration:
                    sequence_counter = last_registration.aantal_items + 1
                else:
                    sequence_counter = 1
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now,
                                                               "aantal_items": sequence_counter})
                if registration:
                    message_sent = False
                    if "auto" in location and location["auto"]: # send message when badge is scanned
                        message_sent = __send_ss_message(registration, location, student)
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id, "sequence_ctr": sequence_counter, "message_sent": message_sent})
                    return ret

            if location["type"] == "toilet":
                last_registration = mregistration.registration_get([("leerlingnummer", "=", student.leerlingnummer), ("location", "=", location_key)], order_by="-id")
                if last_registration:
                    sequence_counter = last_registration.aantal_items + 1
                else:
                    sequence_counter = 1
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now,
                                                               "aantal_items": sequence_counter})
                if registration:
                    ret["data"][0].update({"timestamp": str(registration.time_in), "id": registration.id, "sequence_ctr": sequence_counter})
                    return ret

            log.info(f'{sys._getframe().f_code.co_name}:  {student.leerlingnummer} could not make a registration')
            return {"status": False, "data": "Kan geen nieuwe registratie maken"}
        log.info(f'{sys._getframe().f_code.co_name}:  rif/leerlingnummer {rfid}/{leerlingnummer} not found in database')
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


overview_table_extra_headers = {
    "sms": ["SMS", "Opmerking"],
    "cellphone": ["Bericht", "Aantal", ],
    "toilet": ["Aantal", ],
}


# filters priority (high to low)
# search
# sms/cellphone specific
# period

def registration_get(filters):
    try:
        locations = msettings.get_configuration_setting("location-profiles")
        location_key = filters["filter-location"]
        location = locations[location_key]
        type = location["type"]
        ret = {'status': True, "action": "add", "data": []}
        if filters["search-text"] != "":
            search = filters["search-text"]
        else:
            search = None
        time_low = time_high = selected_day = None
        flag1 = flag2 = None
        # ignore period filter when the sms-specific or cellphone-specific is used
        if search == None:
        # if type == "sms" and filters["sms-specific-select"] == "all" or type == "cellphone" and filters["cellphone-specific-select"] == "all" or type not in ["sms", "cellphone"]:
            if filters["period-select"] == "on-date":
                selected_day = filters["filter-date"]
                if not selected_day:
                    selected_day = str(datetime.datetime.now())
                time_low = datetime.datetime.strptime(selected_day, "%Y-%m-%d").date()
                time_high = time_low + datetime.timedelta(days=1)
            elif filters["period-select"] in ["last-2-months", "last-4-months", "last-week"]:
                delta = 60 if filters["period-select"] == "last-2-months" else 120 if filters["period-select"] == "last-4-months" else 7
                time_low = datetime.datetime.now() - datetime.timedelta(days=delta)
        if "table" in location and location["table"] == "staff":
            # Staff specific data
            ret.update({"headers": ["Tijdstempel", "Naam", "Code"]})
            registrations = mregistration.registration_staff_get(location_key, search=search, time_low=time_low, time_high=time_high)
            for tuple in registrations:
                registration = tuple[0]
                staff = tuple[1]
                item = {
                    "leerlingnummer": staff.code,
                    "naam": staff.naam,
                    "voornaam": staff.voornaam,
                    "klascode": staff.code,
                    "timestamp": str(registration.time_in),
                    "id": registration.id,
                    "photo": "",
                }
                ret["data"].append(item)
            pass
        else:
            # Student specific data
            include_foto = filters["view-layout-select"] == "tile"
            if search == None:
                if type == "sms":
                    flag1 = False if filters["sms-specific-select"] == "no-ack" else None
                    flag2 = False if filters["sms-specific-select"] == "no-sms-sent" else None
                elif type == "cellphone":
                    flag1 = False if filters["cellphone-specific-select"] == "no-message-sent" else None
                if flag1 != None or flag2 != None:
                    time_low = time_high = selected_day = None
            registrations = mregistration.registration_student_photo_get(location_key, search=search, time_low=time_low, time_high=time_high, flag1=flag1, flag2=flag2, include_foto=include_foto)
            headers = ["Tijdstempel", "Naam", "Klas"]
            if type in overview_table_extra_headers:
                headers += overview_table_extra_headers[type]
            ret.update({"headers": headers})
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
                if type == "sms":
                    item.update({"remark": registration.text1, "remark_ack": registration.flag1, "sms_sent": registration.flag2,})
                elif type == "cellphone":
                    item.update({"sequence_ctr": registration.aantal_items, "message_sent": registration.flag1})
                elif type == "toilet":
                    item.update({"sequence_ctr": registration.aantal_items})
                ret["data"].append(item)

            if search != None:
                ret.update({"search": True})
            elif selected_day != None:
                ret.update({"date": selected_day})

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


def api_registration_update(location_key, ids, fields):
    try:
        location_settings = msettings.get_configuration_setting("location-profiles")
        if location_key not in location_settings:
            log.info(f'{sys._getframe().f_code.co_name}:  {location_key} is not valid')
            return {"status": False, "data": f"Locatie {location_key} is niet geldig"}
        location = location_settings[location_key]
        data = []
        for id in ids:
            registration = mregistration.registration_get(("id", "=", id))
            new_fields = {}
            item = {}
            if location["type"] == "sms":
                if "remark" in fields:
                    new_fields["text1"] = fields["remark"]
                    item["remark"] = fields["remark"]
                if "remark_ack" in fields:
                    new_fields["flag1"] = fields["remark_ack"]
                    item["remark_ack"] = fields["remark_ack"]
                if item:
                    item["id"] = id
                    data.append(item)
            mregistration.registration_update(registration, new_fields)
        return {"status": True, "data": data}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def api_registration_send_message(ids, location_key):
    try:
        location_settings = msettings.get_configuration_setting("location-profiles")
        if location_key not in location_settings:
            log.info(f'{sys._getframe().f_code.co_name}:  {location_key} is not valid')
            return {"status": False, "data": f"Locatie {location_key} is niet geldig"}
        location = location_settings[location_key]
        data = []
        for id in ids:
            registration = mregistration.registration_get(("id", "=", id))
            student = mstudent.student_get([("leerlingnummer", "=", registration.leerlingnummer)])
            if student:
                if location["type"] == "sms":
                    data.append({"id": id, "sms_sent": __send_sms(registration, location, student)})
                if location["type"] == "cellphone":
                    data.append({"id": id, "ss_message_sent": __send_ss_message(registration, location, student)})
            else:
                log.error(f'{sys._getframe().f_code.co_name}: could not find student fore registration {id}')
        return {"status": True, "data": data}
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

            locations = msettings.get_configuration_setting("location-profiles")
            artikels = msettings.get_configuration_setting("artikel-profiles")
            location2ppi = {}
            for location, data in locations.items():
                price_per_item = int(artikels[data["artikel"]]["prijs-per-item"]) if "artikel" in data else 0
                location2ppi[location] = price_per_item

            for registration in registrations:
                key = str(registration[0]) + registration[2] + registration[3]
                if key in db_cache:
                    log.info(f'{sys._getframe().f_code.co_name}: registration already present, {registration}')
                    nbr_doubles += 1
                    continue
                new_registrations.append({"leerlingnummer": registration[2], "location": registration[3], "time_in": registration[0], "time_out": registration[1], "prijs_per_item": location2ppi[registration[3]]})
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


def __send_sms(registration, location, student, force=False):
    try:
        receiver = ""
        if not registration.flag2 or force:
            text_body = msettings.get_configuration_setting("sms-student-too-late")
            text_body = text_body.replace("%%VOORNAAM%%", student.voornaam)
            text_body = text_body.replace("%%NAAM%%", student.naam)
            text_body = text_body.replace("%%TIJD%%", str(registration.time_in))
            enable_send_sms = location["enable_sending"]
            if "force_to" in location:  # overwrite sms receivers
                receiver = location["force_to"]
                send_sms(receiver, text_body, enable_send_sms)
            else:
                if student.lpv1_gsm != "":
                    send_sms(student.lpv1_gsm, text_body, enable_send_sms)
                    receiver += student.lpv1_gsm + "/"
                if student.lpv2_gsm != "":
                    send_sms(student.lpv2_gsm, text_body, enable_send_sms)
                    receiver += student.lpv2_gsm
            # flag2: sms is sent
            mregistration.registration_update(registration, {"flag2": True})
            log.info(f'{sys._getframe().f_code.co_name}: SMS ({location["locatie"]}), {student.naam} {student.voornaam} at {registration.time_in}, to {receiver}')
        else:
            log.info(f'{sys._getframe().f_code.co_name}: SMS ({location["locatie"]}), {student.naam} {student.voornaam} NOT sent')
        return registration.flag2
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return False


def __send_ss_message(registration, location, student, force=False):
    try:
        def __process_template(school, id):
            out = {}
            templates = msettings.get_configuration_setting("smartschool-message-templates").split("\n")
            for type in ["ONDERWERP", "INHOUD"]:
                start_subject_tag = f"%%{school}-{id}-{type}-START%%"
                stop_subject_tag = f"%%{school}-{id}-{type}-STOP%%"
                msg = None
                for line in templates:
                    if stop_subject_tag in line: break
                    if msg is not None and msg != "": msg += "\n"
                    if msg is not None: msg += line
                    if start_subject_tag in line: msg = ""
                if msg:
                    msg = msg.replace("%%VOORNAAM%%", student.voornaam)
                    msg = msg.replace("%%NAAM%%", student.naam)
                    msg = msg.replace("%%TIJD%%", str(registration.time_in))
                    msg = msg.replace("%%KLAS%%", str(student.klascode))
                    msg = msg.replace("%%AANTAL-OVERTREDINGEN%%", str(registration.aantal_items))
                out[type] = msg
            return out

        if not registration.flag1 or force:
            ss_internal_numbers = msettings.get_configuration_setting("ss-internal-numbers")
            limit = location["limiet"]
            seq_ctr = registration.aantal_items
            if seq_ctr < (limit - 1): return False
            if seq_ctr > (limit + 1): seq_ctr = limit + 1
            school = student.get_school
            if "force_to" in location:
                tos = location["force_to"]
            else:
                tos = location["to"][school.lower()][seq_ctr]
            ss_tos = []
            for to in tos:
                if to == "ouders":
                    ss_tos += [{"id": student.leerlingnummer, "coaccount": i} for i in range(3)]
                else:
                    staff = mstaff.staff_get(("code", "=", to))
                    if staff:
                        ss_tos.append({"id": staff.ss_internal_nbr, "coaccount": 0})
                    else:
                        if ss_internal_numbers is not None:
                            if to in ss_internal_numbers:
                                ss_tos.append({"id": ss_internal_numbers[to], "coaccount": 0})
                            else:
                                log.error(f'{sys._getframe().f_code.co_name}: Could not find ss internal number of {to}')
                        else:
                            log.error(f'{sys._getframe().f_code.co_name}: Could not find ss internal number/or not defined in settings of {to}')
            message = __process_template(school, seq_ctr)

            enable_sending = location["enable_sending"] if "enable_sending" in location else False
            for to in ss_tos:
                ss_send_message(to["id"], "csu", message["ONDERWERP"], message["INHOUD"], to["coaccount"], enable_sending)
            # flag1: message is sent
            mregistration.registration_update(registration, {"flag1": True})
            log.info(f'{sys._getframe().f_code.co_name}: Smartschool ({location["locatie"]}), {student.naam} {student.voornaam} at {registration.time_in}')
        else:
            log.info(f'{sys._getframe().f_code.co_name}: Smartschool ({location["locatie"]}), {student.naam} {student.voornaam} NOT sent')
        return registration.flag1
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return False
