import app.application.api
from app import log
from app.application.formio import iterate_components_cb
from app.data import student as mstudent, settings as msettings, photo as mphoto, person as mperson
import app.data.settings
from app.application import formio as mformio, email as memail, util as mutil, ad as mad, papercut as mpapercut
import sys, base64


def student_delete(ids):
    mstudent.student_delete_m(ids)


# find the first next vsk number, to be assigned to a student, or -1 when not found
def vsk_get_next_number():
    try:
        student = mstudent.student_get_m({'delete': False}, order_by='-vsknummer', first=True)
        if student and student.vsknummer != '':
            return {"status": True, "data": int(student.vsknummer) + 1}
        else:
            start_number = msettings.get_configuration_setting('cardpresso-vsk-startnumber')
            return {"status": True, "data": start_number}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f'Error: {e}'}


# update students with no vsk number yet.  Start from the given number and increment for each student
# return the number of updated students
def vsk_update_numbers(vsknumber):
    try:
        vsknumber = int(vsknumber)
        changed_students = []
        students = mstudent.student_get_m({'vsknummer': '', 'delete': False})
        nbr_updated = 0
        for student in students:
            changed_students.append({'vsknummer': str(vsknumber), 'student': student, 'changed': ['vsknummer']})
            vsknumber += 1
            nbr_updated += 1
        mstudent.student_change_m(changed_students)
        return {"status": True, "data": nbr_updated}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": f'Error: {e}'}


def vsk_clear_numbers():
    students = mstudent.student_get_m()
    nbr_updated = 0
    for student in students:
        student.vsknummer = ''
        nbr_updated += 1
    mstudent.commit()
    return {"status": True, "data": nbr_updated}


def cront_task_vsk_numbers(opaque=None):
    # check if schooljaar has changed.  If so, clear all vsk numbers first
    schoolyear_changed, _, _ = msettings.get_changed_schoolyear()
    if schoolyear_changed:
        ret = vsk_clear_numbers()
        log.info(f'vsk_numbers_cron_task: deleted {ret["data"]} vsk numbers')
    ret = vsk_get_next_number()
    if ret['status'] and ret['data'] > -1:
        ret = vsk_update_numbers(ret['data'])
        if ret['status']:
            log.info(f'vsk cron task, {ret["data"]} numbers updated')
        else:
            log.error(f'vsk cron task, error: {ret["data"]}')
    else:
        log.error('vsk cron task, error: no vsk numbers available')
        memail.send_inform_message('sdh-inform-emails', "SDH: Vsk nummers", "Waarschuwing, er zijn geen Vsk nummers toegekend (niet beschikbaar?)")


# delete student that is flagged delete
# reset new and changed flags
def student_post_processing(opaque=None):
    try:
        log.info(f'{sys._getframe().f_code.co_name}: START')
        deleted_students = mstudent.student_get_m({"delete": True})
        mstudent.student_delete_m(students=deleted_students)
        log.info(f"deleted {len(deleted_students)} students")
        changed_new_student = mstudent.student_get_m({"-changed": ""})
        changed_new_student.extend(mstudent.student_get_m({"new": True}))
        for student in changed_new_student:
            mstudent.student_update(student, {"changed": "", "new": False}, commit=False)
        mstudent.commit()
        log.info(f"new, changed {len(changed_new_student)} student")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def cron_task_schoolyear_clear_changed_flag(opaque=None):
    msettings.reset_changed_schoolyear()


def klassen_get_unique():
    klassen = mstudent.student_get_m(fields=['klascode'])
    klassen = list(set([k[0] for k in klassen]))
    klassen.sort()
    return klassen


############## api ####################
def api_student_get_fields():
    try:
        return mstudent.get_columns()
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return False


def api_student_get(options=None):
    try:
        return app.application.api.api_get_model_data(mstudent.Student_old, options)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise Exception(f'STUDENT-EXCEPTION {sys._getframe().f_code.co_name}: {e}')


def api_student_update(data):
    try:
        db_ok = papercut_ok = ad_ok = True
        db_student = mstudent.student_get({'id': data['id']})
        if "password_data" in data:
            new_password = data["password_data"]["password"]
            must_change_password = data["password_data"]["must_update"]
            ad_ok = ad_ok and mad.person_set_password(db_student, new_password, must_change_password)
            data["password_data"] = "xxx"
        elif "rfid" in data:
            rfid = data['rfid']
            person = mperson.check_if_rfid_already_exists(data["rfid"])
            if person:
                log.error("FLUSH-TO-EMAIL")  # this will trigger an email with ERROR-logs (if present)
                return {"status": False, "data": f"RFID {rfid} bestaat al voor {person.person_id}"}
        changed_attributes = [k for k, v in data.items() if hasattr(db_student, k) and v != getattr(db_student, k)]
        data = {k: v for k,v in data.items() if k in changed_attributes}
        if data:
            ad_ok = ad_ok and mad.student_update(db_student, data)
            papercut_ok = papercut_ok and mpapercut.person_update(db_student, data)
            db_student = mstudent.student_update(db_student, data)
            db_ok = db_ok and db_student is not None
        if db_ok and ad_ok and papercut_ok:
            log.info(f'{sys._getframe().f_code.co_name}: DB {db_ok}, AD {ad_ok}, PAPERCUT {papercut_ok}, data {data}')
            log.error("FLUSH-TO-EMAIL")  # this will trigger an email with ERROR-logs (if present)
            return {"status": True, "data": f"Student {db_student.person_id} is aangepast"}
        else:
            log.error(f'{sys._getframe().f_code.co_name}: DB {db_ok}, AD {ad_ok}, PAPERCUT {papercut_ok}, data {data}')
            log.error("FLUSH-TO-EMAIL")  # this will trigger an email with ERROR-logs (if present)
            return {"status": False, "data": f"Fout, kan student {db_student.person_id} niet aanpassen."}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        log.error("FLUSH-TO-EMAIL")  # this will trigger an email with ERROR-logs (if present)
        raise Exception(f'STUDENT-EXCEPTION {sys._getframe().f_code.co_name}: {e}')


def api_database_integrity_check(data):
    try:
        ret = {"status": False, "data": "Gelieve minstens één database te selecteren!"}
        if 'ad' in data['databases']:
            if data['event'] == 'event-update-database':
                ret = mad.database_integrity_check(return_log=True, mark_changes_in_db=True)
                if ret['status']:
                    ret = mad.student_process_flagged()
            elif data['event'] == 'event-start-integrity-check':
                ret = mad.database_integrity_check(return_log=True)
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise Exception(f'STUDENT-EXCEPTION {sys._getframe().f_code.co_name}: {e}')

############## formio #########################
def form_prepare_for_view_cb(component, opaque):
        if component['key'] == 'photo':
            component['attrs'][0]['value'] = component['attrs'][0]['value'] + str(opaque['photo'])


def form_prepare_for_view(id, read_only=False):
    try:
        student = mstudent.student_get({"id": id})
        template = app.data.settings.get_configuration_setting('student-formio-template')
        photo = mphoto.photo_get({'filename': student.foto})
        data = {"photo": base64.b64encode(photo.photo).decode('utf-8') if photo else ''}
        iterate_components_cb(template, form_prepare_for_view_cb, data)
        return {'template': template,
                'defaults': student.to_dict()}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise e


def form_prepare_for_edit(form, flat={}, unfold=False):
    def cb(component):
        if component['key'] == 'photo':
            component['attrs'][0]['value'] = component['attrs'][0]['value'] + str(flat['photo'])

    iterate_components_cb(form, cb)
    return form
############ datatables: student overview list #########
def format_data(db_list, total_count=None, filtered_count=None):
    out = []
    for student in db_list:
        em = student.to_dict()
        if student.foto_id == -1:
            em['overwrite_cell_color'] = [['foto', 'pink']]
        em.update({
            'row_action': student.id,
            'DT_RowId': student.id
        })
        out.append(em)
    return total_count, filtered_count, out


def photo_get_nbr_not_found():
    nbr_students_no_photo = mstudent.student_get_m({'foto_id': -1}, count=True)
    return nbr_students_no_photo

