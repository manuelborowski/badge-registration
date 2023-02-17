from app import log, db
import sys
from app.data.models import Warning


def add_warning(data):
    try:
        warning = Warning()
        for k, v in data.items():
            if hasattr(warning, k):
                if getattr(Warning, k).expression.type.python_type == type(v):
                    setattr(warning, k, v.strip() if isinstance(v, str) else v)
        db.session.add(warning)
        db.session.commit()
        return warning
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def delete_warnings(warning_ids):
    try:
        for id in warning_ids:
            warning = Warning.guery.filter(id=id)
            db.session.delete(warning)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def get_first_warning(data={}):
    try:
        guest = get_warnings(data, first=True)
        return guest
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def get_warnings(data={}, special={}, order_by=None, first=False, count=False):
    try:
        q = Warning.query
        for k, v in data.items():
            if hasattr(Warning, k):
                q = q.filter(getattr(Warning, k) == v)
        if order_by:
            q = q.order_by(getattr(Warning, order_by))
        if first:
            warning = q.first()
            return warning
        if count:
            return q.count()
        warnings = q.all()
        return warnings
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def update_warning(warning, data={}):
    try:
        for k, v in data.items():
            if hasattr(warning, k):
                if getattr(Warning, k).expression.type.python_type == type(v):
                    setattr(warning, k, v.strip() if isinstance(v, str) else v)
        db.session.commit()
        return warning
    except Exception as e:
        db.session.rollback()
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return None


def pre_filter():
    return db.session.query(Warning)


def search_data(search_string):
    search_constraints = []
    search_constraints.append(Warning.message.like(search_string))
    return search_constraints


def filter_data(query, filter):
    if 'visible' in filter and filter['visible'] != 'default':
        query = query.filter(Warning.visible == (filter['visible'] == 'True'))
    return query


def format_data(db_list):
    out = []
    for warning in db_list:
        em = warning.flat()
        em.update({
            'row_action': warning.id,
            'id': warning.id,
            'DT_RowId': warning.id
        })
        out.append(em)
    return out


