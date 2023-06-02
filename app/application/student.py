from app.data import settings as msettings, student as mstudent, photo as mphoto, utils as mutils
import sys, requests, base64

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def student_load_from_sdh(opaque=None, **kwargs):
    log.info(f"{sys._getframe().f_code.co_name}, START")
    try:
        # check for new, updated or deleted students
        sdh_student_url = msettings.get_configuration_setting('sdh-student-url')
        sdh_key = msettings.get_configuration_setting('sdh-api-key')
        updated_students = []
        new_students = []
        res = requests.get(sdh_student_url, headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            sdh_students = res.json()
            if sdh_students['status']:
                log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_students["data"])} students from SDH')
                db_students = mstudent.student_get_m()
                db_username_to_student = {s.username: s for s in db_students}
                for sdh_student in sdh_students["data"]:
                    if sdh_student["username"] in db_username_to_student:
                        # check for changed rfid or classgroup
                        db_student = db_username_to_student[sdh_student["username"]]
                        update = {}
                        if db_student.rfid != sdh_student["rfid"]:
                            update["rfid"] = sdh_student["rfid"]
                        if db_student.klascode != sdh_student["klascode"]:
                            update["klascode"] = sdh_student["klascode"]
                        if db_student.middag != sdh_student["middag"]:
                            update["middag"] = sdh_student["middag"]
                        if db_student.foto_id != sdh_student["foto_id"]:
                            update["foto_id"] = sdh_student["foto_id"]
                        if update:
                            update.update({"item": db_student})
                            updated_students.append(update)
                            log.info(f'{sys._getframe().f_code.co_name}, Update student {db_student.username}, update {update}')
                        del(db_username_to_student[sdh_student["username"]])
                    else:
                        new_students.append({"username": sdh_student["username"], "klascode": sdh_student["klascode"], "naam": sdh_student["naam"],
                                             "voornaam": sdh_student["voornaam"], "middag": sdh_student["middag"], "rfid": sdh_student["rfid"], "foto_id": sdh_student["foto_id"]})
                        log.info(f'{sys._getframe().f_code.co_name}, New student {sdh_student["username"]}')
                deleted_students = [v for (k, v) in db_username_to_student.items()]
                for student in deleted_students:
                    log.info(f'{sys._getframe().f_code.co_name}, Delete student {student.username}')
                deleted_photos = [v.foto_id for (k, v) in db_username_to_student.items()]
                mstudent.student_add_m(new_students)
                mstudent.student_update_m(updated_students)
                mstudent.student_delete_m(students=deleted_students)
                mphoto.photo_delete_m(deleted_photos)
                log.info(f'{sys._getframe().f_code.co_name}, students add {len(new_students)}, update {len(updated_students)}, delete {len(deleted_students)}')
            else:
                log.info(f'{sys._getframe().f_code.co_name}, error retrieving students from SDH, {sdh_students["data"]}')
        else:
            log.error(f'{sys._getframe().f_code.co_name}: api call to {sdh_student_url} returned {res.status_code}')

        # check for all students if their photo is changed (different size)
        sdh_photo_size_url = msettings.get_configuration_setting('sdh-photo-size-url')
        db_students = mstudent.student_get_m()
        photo_ids = [str(s.foto_id) for s in db_students]
        sliced_photo_ids = mutils.slice_list(photo_ids, 200)
        photos_to_check = []
        db_photo_sizes = mphoto.photo_get_size_m()
        id_to_photo_size = {p[0]: p[5] for p in db_photo_sizes}
        for slice in sliced_photo_ids:
            res = requests.get(sdh_photo_size_url, params={"ids": ",".join(slice)}, headers={'x-api-key': sdh_key})
            if res.status_code == 200:
                sdh_photo_data = res.json()
                if sdh_photo_data["status"]:
                    log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_photo_data["data"])} photo sizes from SDH')
                    for sdh_photo in sdh_photo_data["data"]:
                        if sdh_photo["id"] in id_to_photo_size:
                            if sdh_photo["size"] != id_to_photo_size[sdh_photo["id"]]:
                                photos_to_check.append(sdh_photo["id"])
                        else:
                            photos_to_check.append(sdh_photo["id"])
                    log.info(f'{sys._getframe().f_code.co_name}, {len(photos_to_check)} photos to check')
                else:
                    log.info(f'{sys._getframe().f_code.co_name}, error retrieving photo sizes from SDH, {sdh_photo_data["data"]}')
            else:
                log.error(f'{sys._getframe().f_code.co_name}: api call to {sdh_photo_size_url} returned {res.status_code}')

        # get the changed photos
        if photos_to_check:
            sdh_photo_url = msettings.get_configuration_setting('sdh-photo-url')
            photo_ids = [str(p) for p in photos_to_check]
            sliced_photo_ids = mutils.slice_list(photo_ids, 200)
            for slice in sliced_photo_ids:
                res = requests.get(sdh_photo_url, params={"ids": ",".join(slice)}, headers={'x-api-key': sdh_key})
                if res.status_code == 200:
                    sdh_photo_data = res.json()
                    if sdh_photo_data["status"]:
                        update_photos = []
                        new_photos = []
                        log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_photo_data["data"])} photos from SDH')
                        for sdh_photo in sdh_photo_data["data"]:
                            id = sdh_photo["id"]
                            decoded_photo = base64.b64decode(sdh_photo["photo"].encode("ascii"))
                            if id in id_to_photo_size:
                                photo = mphoto.photo_get({"id": id})
                                update_photos.append({"item": photo, "photo": decoded_photo})
                                log.info(f'{sys._getframe().f_code.co_name}, Update photo {id}')
                            else:
                                new_photos.append({"id": id, "photo": decoded_photo})
                                log.info(f'{sys._getframe().f_code.co_name}, New photo {id}')
                        mphoto.photo_add_m(new_photos)
                        mphoto.photo_update_m(update_photos)
                        log.info(f'{sys._getframe().f_code.co_name}, {len(update_photos)} photos to update, {len(new_photos)} new photos')
                    else:
                        log.info(f'{sys._getframe().f_code.co_name}, error retrieving photos from SDH, {sdh_photo_data["data"]}')
                else:
                    log.error(f'{sys._getframe().f_code.co_name}: api call to {sdh_photo_url} returned {res.status_code}')
        log.info(f"{sys._getframe().f_code.co_name}, STOP")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

    return True
