from app import flask_app, version
from app.data.settings import get_configuration_setting
from app.application.util import get_api_key
from flask_login import current_user

@flask_app.context_processor
def inject_defaults():
    locations = get_configuration_setting("location-profiles")
    api_key = get_api_key(current_user.level) if current_user.is_active else ""
    return dict(version=f'@ 2022 MB. {version}', title=flask_app.config['HTML_TITLE'], site_name=flask_app.config['SITE_NAME'], stand_alone=flask_app.stand_alone, locations=locations,
                rfidusb_url=flask_app.config["RFIDUSB_API_URL"], api_key=api_key,
                rfidusb_br_url=flask_app.config["RFIDUSB_BR_URL"] if "RFIDUSB_BR_URL" in flask_app.config else "",
                rfidusb_br_key=flask_app.config["RFIDUSB_BR_KEY"] if "RFIDUSB_BR_KEY" in flask_app.config else "")


#called each time a request is received from the client.
# @flask_app.context_processor
# def inject_academic_year():
#     test_server = mutils.return_common_info()
#     return dict(test_server=test_server)
#
