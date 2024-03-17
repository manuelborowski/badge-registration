from app.data import settings as msettings, student as mstudent, photo as mphoto, utils as mutils, registration as mregistration
import sys, requests, base64

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
            registrations = mregistration.registration_get_m([("time_in", ">=", startdate), ("time_in", "<=", enddate), ("location", "=", type2location[balance_type])])
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


        pass
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return 0, 0, 0
