import app.data.formio
from app import db
import app.data.models
from sqlalchemy_serializer import SerializerMixin

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


class Staff(db.Model, SerializerMixin):
    __tablename__ = 'staff'

    date_format = '%Y-%m-%d'
    datetime_format = '%Y-%m-%d %H:%M'
    serialize_rules = ("is_interim_to_text", "is_wisa_to_text",)

    id = db.Column(db.Integer(), primary_key=True)

    voornaam = db.Column(db.String(256), default='')
    naam = db.Column(db.String(256), default='')
    code = db.Column(db.String(256), default='')
    rfid = db.Column(db.String(256), default='')
    ss_internal_nbr = db.Column(db.String(256), default='')

    timestamp = db.Column(db.DateTime)

    new = db.Column(db.Boolean, default=True)
    delete = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)    # long term
    enable = db.Column(db.Boolean, default=True)    # short term
    changed = db.Column(db.TEXT, default='')


def commit():
    return app.data.models.commit()


def staff_add(data = {}, commit=True):
    staff = app.data.models.add_single(Staff, data, commit)
    return staff


def staff_add_m(data = []):
    return app.data.models.add_multiple(Staff, data, timestamp=True)


def staff_update(staff, data={}, commit=True):
    return app.data.models.update_single(Staff, staff, data, commit)


def staff_delete_m(ids=[], staffs=[]):
    return app.data.models.delete_multiple(Staff, ids, staffs)


def staff_get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Staff, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def staff_get(filters=[]):
    return app.data.models.get_first_single(Staff, filters)


def staff_update_m(data = [], overwrite=False):
    return app.data.models.update_multiple(Staff, data, timestamp=True)


############ staff overview list #########
def pre_sql_query():
    return db.session.query(Staff).filter(Staff.active == True)


def pre_sql_filter(query, filter):
    return query


def pre_sql_search(search_string):
    search_constraints = []
    search_constraints.append(Staff.naam.like(search_string))
    search_constraints.append(Staff.voornaam.like(search_string))
    search_constraints.append(Staff.code.like(search_string))
    return search_constraints


