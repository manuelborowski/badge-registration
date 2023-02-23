import datetime, sys, base64
from app.data import student as mstudent, registration as mregistration, utils as mutils, photo as mphoto


#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def registration_add(rfid, location):
    try:
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0)
        student = mstudent.student_get({"rfid": rfid})
        if student:
            photo = mphoto.photo_get({"id": student.foto_id})
            registrations = mregistration.registration_get_m({"username": student.username, "location": location, ">time_in": today}, order_by="id")
            if registrations:
                last_registration = registrations[-1]
                if last_registration.time_out is None:
                    mregistration.registration_update(last_registration, {"time_out": now})
                    log.info(f'{sys._getframe().f_code.co_name}: Badge out, {student.username} at {now}')
                    return {"status": True, "data": {"direction": "uit", "naam": student.naam, "voornaam": student.voornaam, "username": student.username,
                                                     "time":  mutils.datetime_to_dutch_datetime_string(now), "photo": base64.b64encode(photo.photo).decode('utf-8') if photo else ''}}
            registration = mregistration.registration_add({"username": student.username, "location": location, "time_in": now})
            if registration:
                log.info(f'{sys._getframe().f_code.co_name}: Badge in, {student.username} at {now}')
                return {"status": True, "data": {"direction": "in", "naam": student.naam, "voornaam": student.voornaam, "username": student.username,
                                                 "time": mutils.datetime_to_dutch_datetime_string(now), "photo": base64.b64encode(photo.photo).decode('utf-8') if photo else ''}}
            log.info(f'{sys._getframe().f_code.co_name}:  {student.username} could not make a registration')
            return {"status": False, "data": "Kan geen nieuwe registratie maken"}
        log.info(f'{sys._getframe().f_code.co_name}:  {rfid} not found in database')
        return {"status": False, "data": f"Kan student met rfid {rfid} niet vinden in database"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f"Fout, {str(e)}"}


def get_all_actual_registrations(location):
    try:
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0)
        registrations = mregistration.registration_get_m({"location": location, ">time_in": today, "time_out": None}, order_by="id")
        data = []
        for registration in registrations:
            student = mstudent.student_get({"username": registration.username})
            photo = mphoto.photo_get({"id": student.foto_id})
            data.append({
                "username": student.username,
                "naam": student.naam,
                "voornaam": student.voornaam,
                "photo": base64.b64encode(photo.photo).decode('utf-8') if photo and photo.photo else ''
            })
        return data
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def clear_all_registrations(location):
    try:
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0)
        registrations = mregistration.registration_get_m({"location": location, ">time_in": today, "time_out": None}, order_by="id")
        clear_registrations = [{"item": r, "time_out": now} for r in registrations]
        mregistration.registration_update_m(clear_registrations)
        return True
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return False
