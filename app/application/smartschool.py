from app import flask_app
from zeep import Client

#logging on file level
import logging, sys
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())

soap = Client(flask_app.config["SS_API_URL"])


def send_message(to, sender, subject, body, account=0):
    try:
        ret = soap.service.sendMsg(flask_app.config["SS_API_KEY"], to, subject, body, sender, "", account, False)
        log.info(f'{sys._getframe().f_code.co_name}: to {to}, from {sender}, subject {subject}, ret {ret}')
        return ret
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return -1
