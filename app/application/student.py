from app import log
from app.data import settings as msettings, student as mstudent
import sys, requests

def student_load_from_sdh(opaque=None, **kwargs):
    log.info(f"{sys._getframe().f_code.co_name}, START")
    try:
        sdh_student_url = msettings.get_configuration_setting('sdh-student-url')
        sdh_key = msettings.get_configuration_setting('sdh-api-key')
        session = requests.Session()
        res = session.get(sdh_student_url, headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            sdh_students = res.json()

            nbr_student_matching_rijkregister_found = 0
            nbr_student_matching_naam_found = 0
            nbr_student_not_found = 0
            update_students = []
            new_students = []
            deleted_students = []
            if sdh_students['status']:
                log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_students["data"])} students from SDH')
                db_students = mstudent.student_get_m()
                username_to_student = {s.username: s for s in db_students}
                for sdh_student in sdh_students["data"]:
                    if sdh_student["username"] in username_to_student:
                        # check for changed rfid or classgroup
                        db_student = username_to_student[sdh_student["username"]]
                        update = {}
                        if db_student.rfid != sdh_student["rid"]:
                            update["rfid"] = sdh_student["rfid"]
                        if db_student.klascode != sdh_student["klascode"]:
                            update["klascode"] = sdh_student["klascode"]
                        if update:
                            update_students.append(update.update({"id": db_student.id}))
                        del(username_to_student[sdh_student["username"]])
                    else:
                        new_students.append({"username": sdh_student["username"], "klascode": sdh_student["klascode"], "naam": sdh_student["naam"],
                                             "voornaam": sdh_student["voornaam"], "middag": sdh_student["middag"], "rfid": sdh_student["rfid"], "foto_id": sdh_student["foto_id"]})
                deleted_students = [k for (k, v) in db_students]

            #     rijksregister_to_student = {s['rijksregisternummer']: s for s in sdh_students["data"]}
            #     naam_to_student = {s['naam'] + s['voornaam']: s for s in sdh_students["data"]}
            #     log.info(f'{sys._getframe().f_code.co_name}, {len(students)} students in database')
            #     for student in students:
            #         name = student.s_last_name + student.s_first_name
            #         rijksregisternummer = student.s_rijksregister.replace('-', '').replace('.', '')
            #         if rijksregisternummer != "" and rijksregisternummer in rijksregister_to_student:
            #             nbr_student_matching_rijkregister_found += 1
            #             student.klas = rijksregister_to_student[rijksregisternummer]['klascode']
            #             student.s_code = rijksregister_to_student[rijksregisternummer]['leerlingnummer']
            #         elif name in naam_to_student:
            #             nbr_student_matching_naam_found += 1
            #             student.klas = naam_to_student[name]['klascode']
            #             student.s_code = naam_to_student[name]['leerlingnummer']
            #         else:
            #             nbr_student_not_found += 1
            #     mstudent.commit()
            #     log.info(f'{sys._getframe().f_code.co_name}, students, matching rijksregisternummer, found {nbr_student_matching_rijkregister_found}')
            #     log.info(f'{sys._getframe().f_code.co_name}, students, matching naam, found {nbr_student_matching_naam_found}')
            #     log.info(f'{sys._getframe().f_code.co_name}, students not found {nbr_student_not_found}')
            # else:
            #     log.error(f'{sys._getframe().f_code.co_name}: sdh returned {sdh_students["data"]}')

        else:
            log.error(f'{sys._getframe().f_code.co_name}: api call returned {res.status_code}')

        log.info(f"{sys._getframe().f_code.co_name}, STOP")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

    return True
