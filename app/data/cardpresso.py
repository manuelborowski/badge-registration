import sys, json
from app import log, db
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy import delete

class Cardpresso(db.Model, SerializerMixin):
    __tablename__ = 'cardpresso'

    date_format = '%d/%m/%Y'
    datetime_format = '%d/%m/%Y %H:%M'
    serialize_rules = ('-photo',)

    id = db.Column(db.Integer(), primary_key=True)

    voornaam = db.Column(db.String(256), default='')
    naam = db.Column(db.String(256), default='')
    leerlingnummer = db.Column(db.String(256), default='')
    klascode = db.Column(db.String(256), default='')
    middag = db.Column(db.String(256), default='')
    vsknummer = db.Column(db.String(256), default='')
    rfid = db.Column(db.String(256), default = '')
    geboortedatum = db.Column(db.String(256), default='')
    straat = db.Column(db.String(256), default='')
    huisnummer = db.Column(db.String(256), default='')
    busnummer = db.Column(db.String(256), default='')
    gemeente = db.Column(db.String(256), default='')
    photo = db.Column(MEDIUMBLOB)
    schoolnaam = db.Column(db.String(256), default='')
    schooljaar = db.Column(db.String(256), default='')

    new = db.Column(db.Boolean, default=True)
    delete = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    enable = db.Column(db.Boolean, default=True)
    changed = db.Column(db.TEXT, default='')


def commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

def add_badge(data = {}, commit=True):
    try:
        item = Cardpresso()
        for k, v in data.items():
            if hasattr(item, k):
                if getattr(Cardpresso, k).expression.type.python_type == type(v):
                    setattr(item, k, v.strip() if isinstance(v, str) else v)
        db.session.add(item)
        if commit:
            db.session.commit()
        return item
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def add_badges(data = []):
    try:
        for d in data:
            add_badge(d, commit=False)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def delete_badges(ids):
    try:
        statement = delete(Cardpresso).where(Cardpresso.id.in_(ids))
        db.session.execute(statement)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_badges(data={}, order_by=None, first=False, count=False):
    try:
        q = Cardpresso.query
        for k, v in data.items():
            if hasattr(Cardpresso, k):
                q = q.filter(getattr(Cardpresso, k) == v)
        if order_by:
            q = q.order_by(getattr(Cardpresso, order_by))
        if first:
            item = q.first()
            return item
        if count:
            return q.count()
        items = q.all()
        return items
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_first_badge(data={}):
    try:
        item = get_badges(data, first=True)
        return item
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None



############ student overview list #########
def pre_filter():
    return db.session.query(Cardpresso)


def filter_data(query, filter):
    return query


def search_data(search_string):
    search_constraints = []
    search_constraints.append(Cardpresso.naam.like(search_string))
    search_constraints.append(Cardpresso.voornaam.like(search_string))
    search_constraints.append(Cardpresso.leerlingnummer.like(search_string))
    search_constraints.append(Cardpresso.klascode.like(search_string))
    search_constraints.append(Cardpresso.middag.like(search_string))
    return search_constraints

