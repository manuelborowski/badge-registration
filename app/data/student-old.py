import sys, json

import app.data.models
from app import log, db
from sqlalchemy import text, func, desc
from sqlalchemy_serializer import SerializerMixin


class Student_old(db.Model, SerializerMixin):
    __tablename__ = 'students_old'

    date_format = '%d/%m/%Y'
    datetime_format = '%d/%m/%Y %H:%M'

    id = db.Column(db.Integer(), primary_key=True)

    voornaam = db.Column(db.String(256), default='')
    naam = db.Column(db.String(256), default='')
    roepnaam = db.Column(db.String(256), default='')
    rijksregisternummer = db.Column(db.String(256), default='')
    stamboeknummer = db.Column(db.String(256), default='')
    leerlingnummer = db.Column(db.String(256), default='')
    middag = db.Column(db.String(256), default='')
    vsknummer = db.Column(db.String(256), default='')
    rfid = db.Column(db.String(256))
    foto = db.Column(db.String(256), default='')
    foto_id = db.Column(db.Integer, default=-1)

    geboortedatum = db.Column(db.Date)
    geboorteplaats = db.Column(db.String(256), default='')
    geboorteland = db.Column(db.String(256), default='')
    geslacht = db.Column(db.String(256), default='')
    nationaliteit = db.Column(db.String(256), default='')
    straat = db.Column(db.String(256), default='')
    huisnummer = db.Column(db.String(256), default='')
    busnummer = db.Column(db.String(256), default='')
    postnummer = db.Column(db.String(256), default='')
    gemeente = db.Column(db.String(256), default='')
    telefoonnummer = db.Column(db.String(256), default='')
    gsm = db.Column(db.String(256), default='')
    email = db.Column(db.String(256), default='')


    inschrijvingsdatum = db.Column(db.Date)

    schooljaar = db.Column(db.String(256), default='')
    instellingsnummer = db.Column(db.String(256), default='')
    schoolnaam = db.Column(db.String(256), default='')
    klascode = db.Column(db.String(256), default='')
    klasgroep = db.Column(db.String(256), default='')
    adminstratievecode = db.Column(db.String(256), default='')
    klastitularis = db.Column(db.String(256), default='')
    klasnummer = db.Column(db.Integer(), default=0)
    computer = db.Column(db.String(256), default='')
    username = db.Column(db.String(256), default='')


    naamcorrespondentieadres = db.Column(db.String(256), default='')
    aansprekingcorrespondentieadres = db.Column(db.String(256), default='')
    straatcorrespondentieadres = db.Column(db.String(256), default='')
    huisnummercorrespondentieadres = db.Column(db.String(256), default='')
    busnummercorrespondentieadres = db.Column(db.String(256), default='')
    postnummercorrespondentieadres = db.Column(db.String(256), default='')
    woonplaatscorrespondentieadres = db.Column(db.String(256), default='')
    landwoonplaats = db.Column(db.String(256), default='')

    mo_naam = db.Column(db.String(256), default='')
    mo_voornaam = db.Column(db.String(256), default='')
    mo_gsm = db.Column(db.String(256), default='')
    mo_email = db.Column(db.String(256), default='')
    mo_straat = db.Column(db.String(256), default='')
    mo_straat_nr = db.Column(db.String(256), default='')
    mo_straat_bus = db.Column(db.String(256), default='')
    mo_postcode = db.Column(db.String(256), default='')
    mo_gemeente = db.Column(db.String(256), default='')

    va_naam = db.Column(db.String(256), default='')
    va_voornaam = db.Column(db.String(256), default='')
    va_gsm = db.Column(db.String(256), default='')
    va_email = db.Column(db.String(256), default='')
    va_straat = db.Column(db.String(256), default='')
    va_straat_nr = db.Column(db.String(256), default='')
    va_straat_bus = db.Column(db.String(256), default='')
    va_postcode = db.Column(db.String(256), default='')
    va_gemeente = db.Column(db.String(256), default='')

    vo_naam = db.Column(db.String(256), default='')
    vo_voornaam = db.Column(db.String(256), default='')
    vo_straat = db.Column(db.String(256), default='')
    vo_straat_nr = db.Column(db.String(256), default='')
    vo_straat_bus = db.Column(db.String(256), default='')
    vo_postcode = db.Column(db.String(256), default='')
    vo_gemeente = db.Column(db.String(256), default='')

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
    return [p for p in dir(Student_old) if not p.startswith('_')]


def commit():
    return app.data.models.commit()


def student_add(data = {}, commit=True):
    return app.data.models.add_single(Student_old, data, commit)


def student_add_m(data = []):
    return app.data.models.add_multiple(Student_old, data)


def student_update(student, data={}, commit=True):
    return app.data.models.update_single(Student_old, student, data, commit)


def student_delete_m(ids=[], students=[]):
    return app.data.models.delete_multiple(ids, students)


def student_get_m(data={}, fields=[], order_by=None, first=False, count=False, active=True):
    return app.data.models.get_multiple(Student_old, data=data, fields=fields, order_by=order_by, first=first, count=count, active=active)


def student_get(data={}):
    return app.data.models.get_first_single(Student_old, data)



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
                    if getattr(Student_old, property).expression.type.python_type == type(v):
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
    return db.session.query(Student_old).filter(Student_old.active == True)


def pre_sql_filter(query, filter):
    for f in filter:
        if f['name'] == 'photo-not-found':
            if f['value'] == 'not-found':
                query = query.filter(Student_old.foto_id == -1)
        if f['name'] == 'filter-klas':
            if f['value'] != 'default':
                query = query.filter(Student_old.klascode == f['value'])
    return query


def pre_sql_search(search_string):
    search_constraints = []
    search_constraints.append(Student_old.username.like(search_string))
    search_constraints.append(Student_old.computer.like(search_string))
    search_constraints.append(Student_old.roepnaam.like(search_string))
    search_constraints.append(Student_old.naam.like(search_string))
    search_constraints.append(Student_old.voornaam.like(search_string))
    search_constraints.append(Student_old.leerlingnummer.like(search_string))
    search_constraints.append(Student_old.klascode.like(search_string))
    search_constraints.append(Student_old.email.like(search_string))
    return search_constraints