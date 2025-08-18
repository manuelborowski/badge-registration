import sys, qrcode, secrets, base64, io
import app.application.student
from app.data import user as muser, settings as msettings, models as mmodels
from flask import request
from app import flask_app

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


class UserLevel(muser.User.LEVEL):
    pass


def api_user_add(data):
    try:
        user = muser.get_first_user({'username': data['username']})
        if user:
            log.error(f'Error, user {user.username} already exists')
            return {"status": False, "data": f'Fout, gebruiker {user.username} bestaat al'}
        user = muser.add_user(data)
        if 'confirm_password' in data:
            del data['confirm_password']
        if 'password' in data:
            del data['password']
        log.info(f"Add user: {data}")
        return {"status": True, "data": {'id': user.id}}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise Exception(f'USER-EXCEPTION {sys._getframe().f_code.co_name}: {e}')


def api_user_update(data):
    try:
        user = muser.get_first_user({'id': data['id']})
        if user:
            del data['id']
            user = muser.update_user(user, data)
            if user:
                if 'confirm_password' in data:
                    del data['confirm_password']
                if 'password' in data:
                    del data['password']
                log.info(f"Update user: {data}")
                return {"status": True, "data": {'id': user.id}}
        return {"status": False, "data": "Er is iets fout gegaan"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise Exception(f'USER-EXCEPTION {sys._getframe().f_code.co_name}: {e}')


def api_user_delete(data):
    try:
        muser.delete_users(data)
        return {"status": True, "data": "Gebruikers zijn verwijderd"}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise Exception(f'USER-EXCEPTION {sys._getframe().f_code.co_name}: {e}')


def api_user_get(data):
    try:
        user = muser.get_first_user({'id': data['id']})
        return {"status": True, "data": user.to_dict()}
    except Exception as e:
        log.error(data)
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise Exception(f'USER-EXCEPTION {sys._getframe().f_code.co_name}: {e}')


def user_delete(ids):
    muser.delete_users(ids)

def login_url_generate(user):
    try:
        url_token = secrets.token_urlsafe(32)
        user.url_token = url_token
        mmodels.commit()
        return url_token
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return None

def qr_get(user, new_qr=False):
    try:
        if new_qr: user.url_token = None
        url_token = user.url_token if user.url_token else login_url_generate(user)
        root_url = request.root_url
        if "localhost" in root_url:
            # hostname = socket.getfqdn()
            # host_address = socket.gethostbyname_ex(hostname)[2][0]
            # root_url = f"http://{host_address}:{flask_app.config["FLASK_PORT"]}/"
            root_url = flask_app.config["SMARTSCHOOL_OUATH_REDIRECT_URI"]
        # using a token will log the user out when the browser is minimized.
        # Added a smartphone login page to log in using smartschool
        # url = f"{root_url}m/{url_token}"
        url = f"{root_url}m"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4, )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
        return {"qr": img_base64}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": "error", "msg": {str(e)}}

############## formio forms #############
def prepare_add_registration_form():
    try:
        template = msettings.get_configuration_setting('popup-new-update-user')
        return {'template': template,
                'defaults': {'new_password': True}}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise e


def prepare_edit_registration_form(id):
    try:
        user = muser.get_first_user({"id": id})
        template = msettings.get_configuration_setting('popup-new-update-user')
        template = app.application.student.form_prepare_for_edit(template, user.to_dict())
        return {'template': template,
                'defaults': user.to_dict()}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        raise e


############ user overview list #########
def format_data(db_list, total_count=None, filtered_count=None):
    out = []
    for i in db_list:
        em = i.to_dict()
        em.update({"row_action": i.id, "DT_RowId": i.id})
        out.append(em)
    return  total_count, filtered_count, out

