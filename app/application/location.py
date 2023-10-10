from app.data.settings import get_configuration_setting
import sys


#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def get_locations():
    locations = get_configuration_setting("location-profiles")
    ret = {k: l["locatie"] for k, l in locations.items()}
    return ret