from flask import redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user
from sqlalchemy import func

from app import log, flask_app
from . import auth
from .forms import LoginForm
from app.data import user as muser
from app.presentation.layout import utils
from app.application import settings as msettings
import datetime, json, sys

@auth.route(f'/{flask_app.config["AUTO_LOGIN_URL"] if "AUTO_LOGIN_URL" in flask_app.config else "NA1"}', methods=['POST', 'GET'])
def auto_login_generic():
    # remote server, generic auto login
    if "AUTO_LOGIN_URL" in flask_app.config:
        if "AUTO_USER" in flask_app.config:
            user = muser.get_first_user({'username': flask_app.config["AUTO_USER"]})
            login_user(user)
            log.info(u'user {} logged in'.format(user.username))
            user = muser.update_user(user, {"last_login": datetime.datetime.now()})
            if not user:
                log.error('Could not save timestamp')
            return render_template('base.html', default_view=True)
    form = LoginForm(request.form)
    return render_template('auth/login.html', form=form, title='Login', suppress_navbar=True)

@auth.route(f'/{flask_app.config["AUTO_LOGIN_STAFF_REGISTRATION_URL"] if "AUTO_LOGIN_STAFF_REGISTRATION_URL" in flask_app.config else "NA2"}', methods=['POST', 'GET'])
def auto_login_staff_registration():
    # remote server, auto login for staff registration
    if "AUTO_LOGIN_STAFF_REGISTRATION_URL" in flask_app.config:
        if "AUTO_STAFF_REGISTRATION_USER" in flask_app.config:
            user = muser.get_first_user({'username': flask_app.config["AUTO_STAFF_REGISTRATION_USER"]})
            login_user(user)
            log.info(u'user {} logged in'.format(user.username))
            user = muser.update_user(user, {"last_login": datetime.datetime.now()})
            if not user:
                log.error('Could not save timestamp')
            return render_template('register/register.html')
    form = LoginForm(request.form)
    return render_template('auth/login.html', form=form, title='Login', suppress_navbar=True)

@auth.route('/', methods=['POST', 'GET'])
def login():
    # local server, auto login
    if "AUTO_LOGIN" in flask_app.config and flask_app.config["AUTO_LOGIN"]:
        if "AUTO_USER" in flask_app.config:
            user = muser.get_first_user({'username': flask_app.config["AUTO_USER"]})
            login_user(user)
            log.info(u'user {} logged in'.format(user.username))
            user = muser.update_user(user, {"last_login": datetime.datetime.now()})
            if not user:
                log.error('Could not save timestamp')
            return render_template('base.html', default_view=True)

    form = LoginForm(request.form)
    if form.validate() and request.method == 'POST':
        user = muser.get_first_user ({'username': func.binary(form.username.data)})
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            log.info(u'user {} logged in'.format(user.username))
            user = muser.update_user(user, {"last_login": datetime.datetime.now()})
            if not user:
                log.error('Could not save timestamp')
                return redirect(url_for('auth.login'))
            # Ok, continue
            return render_template('base.html', default_view=True)
        else:
            utils.flash_plus(u'Ongeldige gebruikersnaam of paswoord')
            log.error(u'Invalid username/password')
    try:
        return render_template('auth/login.html', form=form, title='Login', suppress_navbar=True)
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return render_template('auth/login.html', form=form, title='Login', suppress_navbar=True)

@auth.route('/logout')
@login_required
def logout():
    log.info(u'User logged out')
    logout_user()
    return redirect(url_for('auth.login'))

SMARTSCHOOL_ALLOWED_BASE_ROLES = [
    'Andere',
    'Leerkracht',
    'Directie'
]

@auth.route('/ss', methods=['POST', 'GET'])
@auth.route('/ss/<string:mobile>', methods=['POST', 'GET'])
def login_ss(mobile=""):
    if 'version' in request.args:
        profile = json.loads(request.args['profile'])

        if not 'username' in profile:  # not good
            log.error(f'Smartschool geeft een foutcode terug: {profile["error"]}')
            return redirect(url_for('auth.login'))

        if profile['basisrol'] in SMARTSCHOOL_ALLOWED_BASE_ROLES:
            # Students are NOT allowed to log in
            user = muser.get_first_user({'username': profile['username'], 'user_type': muser.User.USER_TYPE.OAUTH})
            profile['last_login'] = datetime.datetime.now()
            if user:
                profile['first_name'] = profile['name']
                profile['last_name'] = profile['surname']
                user.email = profile['email']
                user = muser.update_user(user, profile)
            else:
                if msettings.get_configuration_setting('generic-new-via-smartschool'):
                    profile['first_name'] = profile['name']
                    profile['last_name'] = profile['surname']
                    profile['user_type'] = muser.User.USER_TYPE.OAUTH
                    profile['level'] = msettings.get_configuration_setting("generic-new-via-smartschool-default-level")
                    user = muser.add_user(profile)
                else:
                    log.info('New users not allowed via smartschool')
                    return redirect(url_for('auth.login'))
            login_user(user)
            log.info(u'OAUTH user {} logged in'.format(user.username))
            if not user:
                log.error('Could not save user')
                return redirect(url_for('auth.login'))
            # Ok, continue
            if mobile == "m":
                return redirect(url_for('register.m_show'))
            else:
                return render_template('base.html', default_view=True)
    else:
        redirect_uri = f'{flask_app.config["SMARTSCHOOL_OUATH_REDIRECT_URI"]}/ss'
        if mobile == "m":
            redirect_uri += "/m"
        return redirect(f'{flask_app.config["SMARTSCHOOL_OAUTH_SERVER"]}?app_uri={redirect_uri}')

@auth.route('/m/<string:user_token>', methods=['POST', 'GET'])
def login_m_token(user_token):
    try:
        user = muser.get_first_user({'url_token': user_token})
        if user:
            login_user(user)
            log.info(f'User {user.username} logged in')
            return redirect(url_for('register.m_show'))
        return "geen toegang"
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {str(e)}')

@auth.route('/m', methods=['GET'])
def login_m():
    return render_template('m/login.html')

