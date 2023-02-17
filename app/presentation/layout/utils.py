from flask import flash, request
import datetime


#It is possible to give an extra (exception) message
#The python UTF-8 string is encoded to html UTF-8
def flash_plus(message, e=None):
    message = message.replace('\n', '<br>')
    if e:
        flash((f'{message}<br><br>Details:<br>{e}'))
    else:
        flash((f'{message}'))


def button_pressed(button=None):
    if button:
        return 'button-pressed' in request.values and request.values['button-pressed'] == button
    else:
        return request.values['button-pressed'] if 'button-pressed' in request.values else ''



