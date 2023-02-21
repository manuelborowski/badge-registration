import sys, json, datetime
import app.data
from app import log, db
from sqlalchemy import func, delete
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy_serializer import SerializerMixin


class Photo(db.Model, SerializerMixin):
    __tablename__ = 'photos'

    date_format = '%d/%m/%Y'
    datetime_format = '%d/%m/%Y %H:%M'

    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.String(256), default='')
    photo = db.Column(MEDIUMBLOB)
    timestamp = db.Column(db.DateTime)

    new = db.Column(db.Boolean, default=True)
    delete = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    enable = db.Column(db.Boolean, default=True)
    changed = db.Column(db.Boolean, default=False)


def photo_add(data = {}, commit=True):
    return app.data.models.add_single(Photo, data, commit, timestamp=True)


def photo_add_m(data=[]):
    return app.data.models.add_multiple(Photo, data, timestamp=True)


def commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def photo_update_m(data = []):
    return app.data.models.update_multiple(Photo, data, timestamp=True)


def photo_update(filename, data, commit=True):
    try:
        q = db.session.query(Photo)
        q = q.filter(Photo.filename == filename)
        data.update({'timestamp': datetime.datetime.now()})
        q.update(data)
        if commit:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def update_wisa_photos(data = []):
    try:
        for d in data:
            photo = d['photo']
            for property in d['changed']:
                v = d[property]
                if hasattr(photo, property):
                    if getattr(Photo, property).expression.type.python_type == type(v):
                        setattr(photo, property, v.strip() if isinstance(v, str) else v)
            photo.changed = json.dumps(d['changed'])
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def flag_wisa_photos(data = []):
    try:
        for d in data:
            photo = d['photo']
            photo.new = d['new']
            photo.changed = d['changed']
            photo.delete = d['delete']
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def photo_delete_m(ids=None):
    try:
        if ids:
            delete_statement = delete(Photo).where(Photo.id.in_(ids))
            db.session.execute(delete_statement)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def photo_get_m(data={}, special={}, order_by=None, first=False, count=False):
    try:
        q = Photo.query
        for k, v in data.items():
            if hasattr(Photo, k):
                q = q.filter(getattr(Photo, k) == v)
        if order_by:
            q = q.order_by(getattr(Photo, order_by))
        if first:
            guest = q.first()
            return guest
        if count:
            return q.count()
        guests = q.all()
        return guests
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def photo_get(data={}):
    try:
        user = photo_get_m(data, first=True)
        return user
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def photo_get_size_m():
    try:
        q = db.session.query(Photo.id, Photo.filename, Photo.new, Photo.changed, Photo.delete, func.octet_length(Photo.photo))
        q = q.all()
        return q
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


############ photo overview list #########
def pre_filter():
    return db.session.query(Photo)


def filter_data(query, filter):
    return query


def search_data(search_string):
    search_constraints = []
    search_constraints.append(Photo.naam.like(search_string))
    search_constraints.append(Photo.voornaam.like(search_string))
    return search_constraints

