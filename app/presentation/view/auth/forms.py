# -*- coding: utf-8 -*-
#flapp/auth/forms.py

from wtforms import Form, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(Form):
    username = StringField('Gebruikersnaam', validators=[DataRequired()], render_kw={'autofocus': 'true'})
    password = PasswordField('Paswoord', validators=[DataRequired()])
