import sys, json

import app.data.models
from app import log, db
from sqlalchemy import text, func, desc, or_
from sqlalchemy_serializer import SerializerMixin
from app.data.student import Student
from app.data.photo import Photo


class Reservation(db.Model, SerializerMixin):
    __tablename__ = 'reservations'

    date_format = '%d/%m/%Y'
    datetime_format = '%d/%m/%Y %H:%M'

    id = db.Column(db.Integer(), primary_key=True)

    leerlingnummer = db.Column(db.String(256), default='')
    location = db.Column(db.String(256), default='')
    timestamp = db.Column(db.DateTime, default=None)
    item = db.Column(db.String(256), default='')
    data = db.Column(db.String(256), default='')
    valid = db.Column(db.Boolean, default=False)

def commit():
    return app.data.models.commit()


def reservation_add(data = {}, commit=True):
    return app.data.models.add_single(Reservation, data, commit)


def reservation_add_m(data = []):
    return app.data.models.add_multiple(Reservation, data)


def reservation_update(Reservation, data={}, commit=True):
    return app.data.models.update_single(Reservation, Reservation, data, commit)


def reservation_update_m(data={}, commit=True):
    return app.data.models.update_multiple(Reservation, data, commit)


def reservation_delete_m(ids=[], reservations=[]):
    return app.data.models.delete_multiple(Reservation, ids, reservations)


def reservation_get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=None):
    return app.data.models.get_multiple(Reservation, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def reservation_get(filters=[], order_by=None):
    return app.data.models.get_first_single(Reservation, filters, order_by=order_by)