from app.data.settings import get_configuration_setting
import sys


#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())



def get_locations():
    try:
        return get_configuration_setting("location-profiles")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise e
