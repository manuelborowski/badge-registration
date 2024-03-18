import sys, json
import app.data.models
from app import log, db
from sqlalchemy_serializer import SerializerMixin


class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'

    date_format = '%d/%m/%Y'
    datetime_format = '%d/%m/%Y %H:%M'

    id = db.Column(db.Integer(), primary_key=True)

    voornaam = db.Column(db.String(256), default='')
    naam = db.Column(db.String(256), default='')
    roepnaam = db.Column(db.String(256), default='')
    middag = db.Column(db.String(256), default='')
    rfid = db.Column(db.String(256))
    klascode = db.Column(db.String(256), default='')
    klasgroep = db.Column(db.String(256), default='')
    instellingsnummer = db.Column(db.String(256), default='')
    leerlingnummer = db.Column(db.String(256), default='')
    username = db.Column(db.String(256), default='')
    foto_id = db.Column(db.Integer())
    soep = db.Column(db.String(256), default='')
    lpv1_gsm = db.Column(db.String(256), default='')
    lpv2_gsm = db.Column(db.String(256), default='')

    timestamp = db.Column(db.DateTime)

    new = db.Column(db.Boolean, default=True)
    delete = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)    # long term
    enable = db.Column(db.Boolean, default=True)    # short term
    changed = db.Column(db.TEXT, default='')

    @property
    def person_id(self):
        return self.leerlingnummer


def get_columns():
    return [p for p in dir(Student) if not p.startswith('_')]


def commit():
    return app.data.models.commit()


def student_add(data={}, commit=True):
    return app.data.models.add_single(Student, data, commit, timestamp=True)


def student_add_m(data=[]):
    return app.data.models.add_multiple(Student, data, timestamp=True)


def student_update(student, data={}, commit=True):
    return app.data.models.update_single(Student, student, data, commit, timestamp=True)


def student_update_m(data=[]):
    return app.data.models.update_multiple(Student, data, timestamp=True)


def student_delete_m(ids=[], students=[]):
    return app.data.models.delete_multiple(Student, ids, students)


def student_get_m(filters=[], fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Student, filters=filters, fields=fields, order_by=order_by, first=first, count=count, active=active)


def student_get(filters=[]):
    return app.data.models.get_first_single(Student, filters)

############ student overview list #########
def pre_sql_query():
    return db.session.query(Student).filter(Student.active == True)


def pre_sql_filter(query, filter):
    for f in filter:
        if f['name'] == 'photo-not-found':
            if f['value'] == 'not-found':
                query = query.filter(Student.foto_id == -1)
        if f['name'] == 'filter-klas':
            if f['value'] != 'default':
                query = query.filter(Student.klascode == f['value'])
    return query


def pre_sql_search(search_string):
    search_constraints = []
    search_constraints.append(Student.leerlingnummer.like(search_string))
    search_constraints.append(Student.naam.like(search_string))
    search_constraints.append(Student.voornaam.like(search_string))
    search_constraints.append(Student.klascode.like(search_string))
    return search_constraints
