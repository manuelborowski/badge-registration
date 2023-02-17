from flask import redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user
from sqlalchemy import func

from app import log, flask_app
from . import auth
from .forms import LoginForm
from app.data import user as muser
from app.presentation.layout import utils
from app.application import settings as msettings, location as mlocation
import datetime, json

@auth.route('/', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)
    locations = mlocation.get_locations()
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
            return redirect(url_for('student.show'))
        else:
            utils.flash_plus(u'Ongeldige gebruikersnaam of paswoord')
            log.error(u'Invalid username/password')
    return render_template('auth/login.html', form=form, title='Login', locations=locations)


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
def login_ss():
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
                    profile['level'] = muser.User.LEVEL.USER
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
            return redirect(url_for('student.show'))
    else:
        redirect_uri = f'{flask_app.config["SMARTSCHOOL_OUATH_REDIRECT_URI"]}/ss'
        return redirect(f'{flask_app.config["SMARTSCHOOL_OAUTH_SERVER"]}?app_uri={redirect_uri}')
