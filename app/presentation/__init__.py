from app import flask_app, version
from app.data.settings import get_configuration_setting

@flask_app.context_processor
def inject_defaults():
    locations = get_configuration_setting("location-profiles")
    return dict(version=f'@ 2022 MB. {version}', title=flask_app.config['HTML_TITLE'], site_name=flask_app.config['SITE_NAME'], stand_alone=flask_app.stand_alone, locations=locations,
                rfidusb_url=flask_app.config["RFIDUSB_URL"])




#called each time a request is received from the client.
# @flask_app.context_processor
# def inject_academic_year():
#     test_server = mutils.return_common_info()
#     return dict(test_server=test_server)
#
