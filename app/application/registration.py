import datetime, sys, base64
import app.application.api
import app
from app.data import student as mstudent, registration as mregistration, utils as mutils, photo as mphoto, settings as msettings


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
            popup_delay = msettings.get_configuration_setting("generic-register-popup-delay")
            location_settings = msettings.get_configuration_setting("location-profiles")
            if location_key not in location_settings:
                log.info(f'{sys._getframe().f_code.co_name}:  {location_key} is not valid')
                return {"status": False, "data": f"Locatie {location_key} is niet geldig"}
            location = location_settings[location_key]

            if location["type"] == "nietverplicht":
                registrations = mregistration.registration_get_m([("leerlingnummer", "=", student.leerlingnummer), ("location", "=", location_key), ("time_in", ">", today)], order_by="id")
                if registrations:
                    last_registration = registrations[-1]
                    if last_registration.time_out is None:
                        mregistration.registration_update(last_registration, {"time_out": now})
                        log.info(f'{sys._getframe().f_code.co_name}: Badge out, {student.leerlingnummer} at {now}')
                        return {"status": True, "data": {"direction": "uit", "popup_delay": popup_delay, "photo": photo, "student": student, "registration": last_registration}}
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: Badge in, {student.leerlingnummer} at {now}')
                    return {"status": True, "data": {"direction": "in", "popup_delay": popup_delay, "photo": photo, "student": student, "registration": registration}}
            if location["type"] == "verkoop":
                artikel = msettings.get_configuration_setting("artikel-profiles")[location["artikel"]]
                nbr_items = 1
                registration = mregistration.registration_add({"leerlingnummer": student.leerlingnummer, "location": location_key, "time_in": now,
                                                               "prijs_per_item": artikel["prijs-per-item"], "aantal_items": nbr_items})
                if registration:
                    log.info(f'{sys._getframe().f_code.co_name}: Verkoop({location["locatie"]}), {student.leerlingnummer} at {now}, price-per-item {artikel["prijs-per-item"]}, nbr items {nbr_items}')
                    return {"status": True, "data": {"direction": "in", "popup_delay": popup_delay, "photo": photo, "student": student, "registration": registration}}

            log.info(f'{sys._getframe().f_code.co_name}:  {student.leerlingnummer} could not make a registration')
            return {"status": False, "data": "Kan geen nieuwe registratie maken"}
        log.info(f'{sys._getframe().f_code.co_name}:  {rfid} not found in database')
        return {"status": False, "data": f"Kan student met rfid {rfid} niet vinden in database"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f"Fout, {str(e)}"}


def get_current_registrations(location):
    try:
        now = datetime.datetime.now()
        today = now.date()
        registrations = mregistration.registration_get_m([("location", "=", location), ("time_in", ">", today), ("time_out", "=", None)], order_by="id")
        data = []
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
        return data
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


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
