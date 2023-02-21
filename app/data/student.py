import sys, json, datetime

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
    username = db.Column(db.String(256), default='')
    foto_id = db.Column(db.Integer())
    timestamp = db.Column(db.DateTime)

    new = db.Column(db.Boolean, default=True)
    delete = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)    # long term
    enable = db.Column(db.Boolean, default=True)    # short term
    changed = db.Column(db.TEXT, default='')

    @property
    def person_id(self):
        return self.username


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


def student_get_m(data={}, fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Student, data=data, fields=fields, order_by=order_by, first=first, count=count, active=active)


def student_get(data={}):
    return app.data.models.get_first_single(Student, data)



# data is a list, with:
# student: the ORM-student-object
# changed: a list of properties that are changed
# property#1: the first property changed
# property#2: ....
# overwrite: if True, overwrite the changed field, else extend the changed field
def student_change_m(data=[], overwrite=False):
    try:
        for d in data:
            student = d['student']
            for property in d['changed']:
                v = d[property]
                if hasattr(student, property):
                    if getattr(Student, property).expression.type.python_type == type(v):
                        setattr(student, property, v.strip() if isinstance(v, str) else v)
            # if the student is new, do not set the changed flag in order not to confuse other modules that need to process the students (new has priority over changed)
            if student.new:
                student.changed = ''
            else:
                if overwrite:
                    student.changed = json.dumps(d['changed'])
                else:
                    changed = json.loads(student.changed) if student.changed != '' else []
                    changed.extend(d['changed'])
                    changed = list(set(changed))
                    student.changed = json.dumps(changed)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def student_flag_m(data=[]):
    try:
        for d in data:
            student = d['student']
            for k, v in d.items():
                if hasattr(student, k):
                    setattr(student, k, v)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


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
    search_constraints.append(Student.username.like(search_string))
    search_constraints.append(Student.computer.like(search_string))
    search_constraints.append(Student.roepnaam.like(search_string))
    search_constraints.append(Student.naam.like(search_string))
    search_constraints.append(Student.voornaam.like(search_string))
    search_constraints.append(Student.leerlingnummer.like(search_string))
    search_constraints.append(Student.klascode.like(search_string))
    search_constraints.append(Student.email.like(search_string))
    return search_constraints