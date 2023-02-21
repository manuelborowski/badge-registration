import sys, json

import app.data.models
from app import log, db
from sqlalchemy import text, func, desc
from sqlalchemy_serializer import SerializerMixin


class Registration(db.Model, SerializerMixin):
    __tablename__ = 'registrations'

    date_format = '%d/%m/%Y'
    datetime_format = '%d/%m/%Y %H:%M'

    id = db.Column(db.Integer(), primary_key=True)

    username = db.Column(db.String(256), default='')
    location = db.Column(db.String(256), default='')
    time_in = db.Column(db.DateTime, default=None)
    time_out = db.Column(db.DateTime, default=None)

    new = db.Column(db.Boolean, default=True)
    delete = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    enable = db.Column(db.Boolean, default=True)
    changed = db.Column(db.Boolean, default=False)


def get_columns():
    return [p for p in dir(Registration) if not p.startswith('_')]


def commit():
    return app.data.models.commit()


def registration_add(data = {}, commit=True):
    return app.data.models.add_single(Registration, data, commit)


def registration_add_m(data = []):
    return app.data.models.add_multiple(Registration, data)


def registration_update(registration, data={}, commit=True):
    return app.data.models.update_single(Registration, registration, data, commit)


def registration_delete_m(ids=[], registrations=[]):
    return app.data.models.delete_multiple(ids, registrations)


def registration_get_m(data={}, fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Registration, data=data, fields=fields, order_by=order_by, first=first, count=count, active=active)


def registration_get(data={}):
    return app.data.models.get_first_single(Registration, data)



# data is a list, with:
# Registration: the ORM-Registration-object
# changed: a list of properties that are changed
# property#1: the first property changed
# property#2: ....
# overwrite: if True, overwrite the changed field, else extend the changed field
def registration_change_m(data=[], overwrite=False):
    try:
        for d in data:
            Registration = d['Registration']
            for property in d['changed']:
                v = d[property]
                if hasattr(Registration, property):
                    if getattr(Registration, property).expression.type.python_type == type(v):
                        setattr(Registration, property, v.strip() if isinstance(v, str) else v)
            # if the Registration is new, do not set the changed flag in order not to confuse other modules that need to process the Registrations (new has priority over changed)
            if Registration.new:
                Registration.changed = ''
            else:
                if overwrite:
                    Registration.changed = json.dumps(d['changed'])
                else:
                    changed = json.loads(Registration.changed) if Registration.changed != '' else []
                    changed.extend(d['changed'])
                    changed = list(set(changed))
                    Registration.changed = json.dumps(changed)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def registration_flag_m(data=[]):
    try:
        for d in data:
            Registration = d['Registration']
            for k, v in d.items():
                if hasattr(Registration, k):
                    setattr(Registration, k, v)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


############ Registration overview list #########
def pre_sql_query():
    return db.session.query(Registration).filter(Registration.active == True)


def pre_sql_filter(query, filter):
    for f in filter:
        if f['name'] == 'photo-not-found':
            if f['value'] == 'not-found':
                query = query.filter(Registration.foto_id == -1)
        if f['name'] == 'filter-klas':
            if f['value'] != 'default':
                query = query.filter(Registration.klascode == f['value'])
    return query


def pre_sql_search(search_string):
    search_constraints = []
    search_constraints.append(Registration.username.like(search_string))
    search_constraints.append(Registration.computer.like(search_string))
    search_constraints.append(Registration.roepnaam.like(search_string))
    search_constraints.append(Registration.naam.like(search_string))
    search_constraints.append(Registration.voornaam.like(search_string))
    search_constraints.append(Registration.leerlingnummer.like(search_string))
    search_constraints.append(Registration.klascode.like(search_string))
    search_constraints.append(Registration.email.like(search_string))
    return search_constraints
