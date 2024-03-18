from app.data import settings as msettings, student as mstudent, photo as mphoto, utils as mutils, registration as mregistration
import sys, requests, base64, pandas as pd, re

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


type2location = {"sui-drank": "suidrank", "sul-drank": "suldrank"}

def get_balance(balance_type, startdate, enddate):
    try:
        data = []
        [school, type] = balance_type.split("-")
        startdate = startdate.split("T")[0]
        enddate = enddate.split("T")[0]
        db_students = mstudent.student_get_m()
        if school == "sum":
            leerlingnummers = [s.leerlingnummer for s in db_students if s.klascode[0] in ["1", "2"]]
        elif school == "sul":
            leerlingnummers = [s.leerlingnummer for s in db_students if s.klascode[0] in ["3", "4", "5", "6", "O"] and s.instellingsnummer == "30593"]
        elif school == "sui":
            leerlingnummers = [s.leerlingnummer for s in db_students if s.klascode[0] in ["3", "4", "5", "6", "7"] and s.instellingsnummer == "30569"]
        else:
            leerlingnummers = []
        if balance_type in type2location:
            registrations = mregistration.registration_get_m([("time_in", ">=", startdate), ("time_in", "<=", f"{enddate}T23:59"), ("location", "=", type2location[balance_type])])
            lln2data = {}
            for registation in registrations:
                if registation.leerlingnummer in leerlingnummers:
                    if registation.leerlingnummer in lln2data:
                        lln2data[registation.leerlingnummer]["nbr"] += 1
                    else:
                        lln2data[registation.leerlingnummer] = {"nbr": 1, "price": registation.prijs_per_item}
            data = [f"{k};{v['nbr']};{v['price']/100}" for k, v in lln2data.items()]
        data_text = "\n".join(data)
        filename = f"{balance_type}-{startdate}-{enddate}.txt"
        return data_text, filename
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return f"error: {str(e)}", "error.txt"


maand2index = ["jan", "feb", "mrt", "apr", "jun", "jul", "aug", "sept", "okt", "nov", "dec"]
papercut_data = {}

def papercut_upload(files):
    try:
        global papercut_data
        papercut_data["data"] = []
        for file in files:
            lines = file.read().decode("ansi")
            lines = lines.split("\n")

            lines.pop(0) # comment
            date = lines.pop(0)
            #line 1 contains start and end date
            [d, m, y] = re.search("Vanaf datum = (.*) 0:00:00", date).group(1).split("-")
            m = maand2index.index(m) + 1
            papercut_data["startdate"] = f"{y}{m:02}{int(d):02}"
            [d, m, y] = re.search("Tot datum = (.*) 23:59", date).group(1).split("-")
            m = maand2index.index(m) + 1
            papercut_data["enddate"] = f"{y}{m:02}{int(d):02}"
            header = lines.pop(0) # header
            for total_pages_index, f in enumerate(header.split(";")):
                if f == "Totaal aantal afgedrukte Pagina's":
                    break

            students = mstudent.student_get_m()
            username2student = {s.username.lower(): s for s in students}
            for line in lines:
                fields = line.split(";")
                if fields[0].lower() in username2student:
                    student = username2student[fields[0].lower()]
                    if student.klascode[0] in ["1", "2"]:
                        deelschool = "sum"
                    elif student.instellingsnummer == "30593":
                        deelschool = "sul"
                    else:
                        deelschool = "sui"
                    papercut_data["data"].append({"leerlingnummer": student.leerlingnummer, "deelschool": deelschool, "nbr_pages": fields[total_pages_index]})
                else:
                    log.info(f"Not found, {fields[0].lower()}")
        return {"status": True, "data": "downloaded"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def papercut_export(type):
    try:
        global papercut_data
        data = []
        for item in papercut_data["data"]:
            if item["deelschool"] == type:
                data.append(f"{item['leerlingnummer']};{item['nbr_pages']};0.05")
        data_text = "\n".join(data)
        filename = f"{type}-afdrukken-{papercut_data['startdate']}-{papercut_data['enddate']}.txt"
        return data_text, filename
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return f"error: {str(e)}", "error.txt"

