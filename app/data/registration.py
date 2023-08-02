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

    leerlingnummer = db.Column(db.String(256), default='')
    location = db.Column(db.String(256), default='')
    time_in = db.Column(db.DateTime, default=None)
    time_out = db.Column(db.DateTime, default=None)
    active = db.Column(db.Boolean, default=True)
    aantal_items = db.Column(db.Integer, default=1)
    prijs_per_item = db.Column(db.Integer, default=100) # eurocents


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


def registration_update_m(data={}, commit=True):
    return app.data.models.update_multiple(Registration, data, commit)


def registration_delete_m(ids=[], registrations=[]):
    return app.data.models.delete_multiple(Registration, ids, registrations)


def registration_get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Registration, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def registration_get(filters=[]):
    return app.data.models.get_first_single(Registration, filters)


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
    search_constraints.append(Registration.leerlingnummer.like(search_string))
    search_constraints.append(Registration.computer.like(search_string))
    search_constraints.append(Registration.roepnaam.like(search_string))
    search_constraints.append(Registration.naam.like(search_string))
    search_constraints.append(Registration.voornaam.like(search_string))
    search_constraints.append(Registration.leerlingnummer.like(search_string))
    search_constraints.append(Registration.klascode.like(search_string))
    search_constraints.append(Registration.email.like(search_string))
    return search_constraints
