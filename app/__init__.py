from flask import Flask, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_jsglue import JSGlue
from werkzeug.routing import IntegerConverter as OrigIntegerConvertor
import logging.handlers, os, sys
from functools import wraps
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler
from flask_mail import Mail

flask_app = Flask(__name__, instance_relative_config=True, template_folder='presentation/templates/')

# Configuration files...
from config import app_config
config_name = os.getenv('FLASK_CONFIG')
config_name = config_name if config_name else 'production'
flask_app.config.from_object(app_config[config_name])
flask_app.config.from_pyfile('config.py')

# V0.1: based on school-data-hub V1.3
# 0.2: first working version
# 0.3: clean-up settings.  Bugfixed empty locations
# 0.4: badge-registration-popup-delay: make it a setting
# 0.5: Bugfix Smartschool OAuth2
# 0.6: Show status when badging by changing the backgroundcolor for a short amount of time.
# 0.7: added select to resize photos.  Add classgroup to caption.
# 0.8: added registered counter
# 0.9: bugfix, take also changed photo_id into account
# 0.10: replace username with leerlingnummer (informat pointer)
# 0.11: update api.  Added location-type "verkoop"
# 0.12: update model filtering and api
# 0.13 bugfix location-profiles, add info page for api
# 0.14: clean up.  Added "articles"
# 0.15: bugfix registration, take artikel into account
# 0.16: renamed files to split up into different functions (verkoop, registratie).  Small bugfixes.
# 0.17: added a sorting-select
# 0.18: use socketio-rooms to make sure registrations are visible on the appropriate pages only.
# 0.19: overview: filter on timestamp
# 0.20: small bugfixes.  Registrations can be deleted.
# 0.21: clean up right-click.  Added table with students and added possibility to add a registration via this table.
# 0.22: added location to badge-screen.  Bugfixed and simplified badge-screen.
# 0.23: overview, add day-filter
# 0.24: bufix, add file to git
# 0.25: bufix, add file to git
# 0.26: added timestamp to registration
# 0.27: small bugfixes
# 0.28: show dummy photo if required
# 0.29: when sorting on timestamp, reverse order (oldest first)
# 0.30: add busy indication
# 0.31: add api to get locations
# 0.32: bugfix
# 0.33: gevent/greenlet update.  Implemented auto-login
# 0.34: change navbar color when local server
# 0.35: backup.  Implemented sync, but not ready yet
# 0.36: local badgereader, sync with remote server
# 0.37: after syncing, remove registrations
# 0.38: clean up
# 0.39: cron_task, execute in flask-app-context
# 0.40: small bugfix in pagination.  Added support for articles, allowed only on certain days of the week (daymask).
# 0.41: update navbar
# 0.42: bugfix when adding new data in column soep.  Reworked registration and student syncing
# 0.43: sync locations and articles
# 0.44: added location-select in navbar
# 0.45: implement rfidusb heartbeat, remove location-select if rfidusb-server is not running, color orange if no badgereader is connect to usb.
# 0.46: badgreader can update br-url and br-key
# 0.47: default page after login.  Added sms-registration.  Bugfix import new students.
# 0.48: reworked api-key.  Added update button (not implemented yet)
# 0.49: added support for smsAPI
# 0.50: updated location selector
# 0.51: update requirements.txt
# 0.52: create autologin url
# 0.53: added sms-to-field to test.
# 0.53-export_leerling_rekening-0.1: bugfix standalone with server, take correct price-per-item into account.  Export student balances
# 0.53-export_leerling_rekening-0.2: Make enddate until-and-included iso until
# 0.53-export_leerling_rekening-0.3: added export of papercut overview
# 0.53-export_leerling_rekening-0.4: dateformat: add leading 0 if needed.
# 0.53-export_leerling_rekening-0.5: small updates
# 0.54: reworked navbar.  Reworked context-menu
# 0.55: implemented context-remark and tooltip.
# 0.55-major-rework-0.2: reworked remark-popup, changed to update-items-in-list-of-registrations iso update-remark.
# 0.55-major-rework-0.3: overview update, added fields (sms-sent, remark-acked).  Take into account when 2 browsers, same location but different date, can handle socketio requests (registration updates)
# 0.55-major-rework-0.4: reworked filters, put in seperate file
# 0.55-major-rework-0.5: minor updates.  Added concept of extra-filters
# 0.55-major-rework-0.6: small updates.  Added filter on registrations.
# 0.55-major-rework-0.7: extra-filters, set to default value if they're hidden.
# 0.55-major-rework-0.8: sms get status, update (bugfix) filtering.
# 0.55-major-rework-0.9: added yaml to configure locations.  Added config-flag to disable sending sms
# 0.55-major-rework-0.10: cleanup of login page.
# 0.55-major-rework-0.11: Added input field to search for surname, first name
# 0.55-major-rework-0.12: updated filters.  Added location cellphone.  Reworked context-menu.  Optimized get_current_registrations, skip photo's if not required.
# 0.55-major-rework-0.13: bugfixed user menu
# 0.55-major-rework-0.14: when adding registration from student-table, use leerlingnummer iso rfid.
# 0.55-major-rework-0.15: cellphone, change colours.
# 0.55-major-rework-0.16: bugfix.  In student-tab, make current location only visible.
# 0.55-major-rework-0.17: bugfix, when manually adding a registration for a student, use the view-location iso the badge-location.
# 0.55-major-rework-0.18: reworked frontend
# 0.55-major-rework-0.19: added logging
# 0.55-major-rework-0.20: add period filter to all locations.  If rfid-location is changed, update view-location accordingly.
# 0.55-major-rework-0.21: context-menu, select items depending on layout.  Updated period select.  Bugfix context-menu ico tiles.
# 0.55-major-rework-0.22: cellphone, do not send message twice, updated table.
# 0.55-major-rework-0.23: merge
# 0.55-major-rework-0.24: clear all reservations after syncing with SDH
# 0.55-major-rework-0.25: added mapping for smartschoolaccounts that are not in SDH.  Added enable_sending flag.
# 0.55-major-rework-0.26: sms-specific, small updates
# 0.55-major-rework-0.26-python-3.12-0.1: in flask_jsglue.py, change to "from markupsafe import Markup"
# 0.55-major-rework-0.26-python-3.12-0.2: small update
# 0.55-major-rework-0.27: merge from 0.55-major-rework-0.26-python-3.12-0.2
# 0.55-major-rework-0.27: sms-specific, small updates
# 0.55-major-rework-0.28: template update
# 0.55-major-rework-0.29: merge from 0.55-major-rework-0.26-python-3.12-0.2
# 0.55-major-rework-0.30: merge from 0.55-major-rework-0.26-python-3.12-0.2
# 0.56: merge from 0.55-major-rework-0.30
# 0.57: cleanup after merge.  Small bugfixes due to update to latest version of Flask
# 0.58: export student balance, update and bugfix.
# 0.59: update requirements.txt
# 0.60: update requirements.txt
# 0.61: small bugfix
# 0.62: standalone, sync reservations with SDH.  small bugfix in saving YAML
# 0.63: The badge-location-select (in the navbar) is visible only on the overview page.
# 0.64: add dummy location (new-rfid) that is set when the students page is displayed, this to avoid accidentally adding a registration.  Bugfix updating the "soep" field
# 0.65: when both the overview and students page are opened in seperate tab, select the correct location depending on the visibility of the tab.  Small update when making an RFID reservation
# 0.66: small bugfix when saving yaml
# 0.67: add location-type toilet
# 0.68: bugfixed sw-update.
# 0.69: reworked version-update
# 0.70: reworked version-update
# 0.71: small bugfix
# 0.72: refactored rfid-usb.  Added cors for datatables.
# 0.72-time-registration-0.1: take user-level into account when creating the select-list of locations.  Started with timeregistration.  Added user secretariaat+
# 0.72-time-registration-0.2: added option "inout" to timeregistration.  Timeregistration is up and running.
# 0.73: merged from 0.72-time-registration-0.2
# 0.74: small bugifx
# 0.75: auto-reload page to reset socketio
# 0.76: small updates in auto-reload
# 0.77: firefox specific update
# 0.78: export student print balance, added support for US_en
# 0.79: export registrations.  Optimized context-menu
# 0.80:
# -scketio: set cors to *
# -added jina include for generic popup
# -added misc.js for common functions
# -added unicast socketio channel for generic warnings/popups/messages
# -added heartbeat-code to check the server status and autorelead in case the server comes back up
# -registration_add: major rework to split return messages, unicast to terminals, multicast (group) to client's overview page
# 0.81: update of heartbeat to cover cornercases
# 0.82: small update
# 0.83: new rfid (for student) is directly pushed to sdh
# 0.84: ignore inactive registrations.
# 0.85: added menu option to reset counters of a location
# 0.86: small bugfix when creating default account in database
# 0.87: timeregistrations, add extra columns: starthour, endhour
# 0.88: timeregistration, bufix and added columns
# 0.89: small update

version = "0.89"

db = SQLAlchemy()
login_manager = LoginManager()

#  The original werkzeug-url-converter cannot handle negative integers (e.g. asset/add/-1/1)
class IntegerConverter(OrigIntegerConvertor):
    regex = r'-?\d+'
    num_convert = int


# set up logging
log_werkzeug = logging.getLogger('werkzeug')
log_werkzeug.setLevel(flask_app.config['WERKZEUG_LOG_LEVEL'])
# log_werkzeug.setLevel(logging.ERROR)

#  enable logging
top_log_handle = flask_app.config['LOG_HANDLE']
log = logging.getLogger(top_log_handle)
# support custom filtering while logging
class MyLogFilter(logging.Filter):
    def filter(self, record):
        record.username = current_user.username if current_user and current_user.is_active else 'NONE'
        return True

LOG_FILENAME = os.path.join(sys.path[0], f'log/{flask_app.config["LOG_FILE"]}.txt')
try:
    log_level = getattr(logging, app_config[config_name].LOG_LEVEL)
except:
    log_level = getattr(logging, 'INFO')
log.setLevel(log_level)
log.addFilter(MyLogFilter())
log_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(username)s - %(name)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)


email_log_handler = None
def subscribe_email_log_handler_cb(cb):
    global email_log_handler
    email_log_handler = cb


# if the log-error-message is FLUSH-TO-EMAIL, all error logs are emailed and the buffer is cleared.
class MyBufferingHandler(logging.handlers.BufferingHandler):
    def flush(self):
        if len(self.buffer) > 1:
            message_body = ""
            for b in self.buffer:
                message_body += self.format(b) + "<br>"
            with flask_app.app_context():
                if email_log_handler:
                    email_log_handler(message_body)
        self.buffer = []

    def shouldFlush(self, record):
        return record.msg == "FLUSH-TO-EMAIL"


buf_handler = MyBufferingHandler(2)
buf_handler.setLevel("ERROR")
log.addHandler(buf_handler)
buf_handler.setFormatter(log_formatter)

flask_app.stand_alone = flask_app.config["STAND_ALONE_SERVER"] if "STAND_ALONE_SERVER" in flask_app.config else False

log.info(f"start {flask_app.config['SITE_NAME']}")


jsglue = JSGlue(flask_app)
db.app = flask_app  #  hack:-(
db.init_app(flask_app)

socketio = SocketIO(flask_app, async_mode=flask_app.config['SOCKETIO_ASYNC_MODE'], ping_timeout=10, ping_interval=5, cors_allowed_origins="*")

# configure e-mailclient
email = Mail(flask_app)
send_emails = False
flask_app.extensions['mail'].debug = 0


def create_admin():
    with flask_app.app_context():
        try:
            from app.data.user import User
            find_admin = User.query.filter(User.username == 'admin').first()
            if not find_admin:
                admin = User(username='admin', password='admin', level=User.LEVEL.ADMIN, user_type=User.USER_TYPE.LOCAL)
                db.session.add(admin)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            log.error(f'{sys._getframe().f_code.co_name}: {e}')


flask_app.url_map.converters['int'] = IntegerConverter
login_manager.init_app(flask_app)
login_manager.login_message = 'Je moet aangemeld zijn om deze pagina te zien!'
login_manager.login_view = 'auth.login'

migrate = Migrate(flask_app, db)

SCHEDULER_API_ENABLED = True
ap_scheduler = APScheduler()
ap_scheduler.init_app(flask_app)
ap_scheduler.start()

if 'db' in sys.argv:
    from app.data import models
else:
    create_admin()  #  Only once

    # decorator to grant access to admins only
    def admin_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_at_least_admin:
                abort(403)
            return func(*args, **kwargs)
        return decorated_view


    # decorator to grant access to at least supervisors
    def supervisor_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_at_least_supervisor:
                abort(403)
            return func(*args, **kwargs)
        return decorated_view

    from app.presentation.view import auth, user, settings,  api, warning, register, overview, student
    flask_app.register_blueprint(api.api)
    flask_app.register_blueprint(overview.overview)
    flask_app.register_blueprint(register.register)
    flask_app.register_blueprint(auth.auth)
    flask_app.register_blueprint(user.user)
    flask_app.register_blueprint(student.student)
    flask_app.register_blueprint(settings.settings)
    flask_app.register_blueprint(warning.warning)

    @flask_app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', title='Forbidden'), 403

    @flask_app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html', title='Page Not Found'), 404

    @flask_app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html', title='Server Error'), 500

    @flask_app.route('/500')
    def error_500():
        abort(500)


