import app.application.registration
from . import student
from app import log
from flask import redirect, url_for, request, render_template
from flask_login import login_required, current_user
from app.data.datatables import DatatableConfig
from app.presentation.view import datatables
from app.application import settings as msettings
import json
import app.data
import app.application.student


@student.route('/student/student', methods=['POST', 'GET'])
@login_required
def show():
    # start = datetime.datetime.now()
    ret = datatables.show(table_config, template="student/student.html")
    # print('student.show', datetime.datetime.now() - start)
    return ret


@student.route('/student/table_ajax', methods=['GET', 'POST'])
@login_required
def table_ajax():
    # start = datetime.datetime.now()
    ret =  datatables.ajax(table_config)
    # print('student.table_ajax', datetime.datetime.now() - start)
    return ret


@student.route('/student/table_action', methods=['GET', 'POST'])
@student.route('/student/table_action/<string:action>', methods=['GET', 'POST'])
@student.route('/student/table_action/<string:action>/<string:ids>', methods=['GET', 'POST'])
@login_required
def table_action(action, ids=None):
    if ids:
        ids = json.loads(ids)
    return redirect(url_for('student.show'))


def get_filters():
    klassen = app.application.student.klassen_get_unique()
    klassen = [[k, k] for k in klassen]
    klas_choices = [['default', 'Alles']] + klassen
    return [
        {
            'type': 'select',
            'name': 'filter-klas',
            'label': 'Klassen',
            'choices': klas_choices,
            'default': 'default',
        },
    ]


class Config(DatatableConfig):
    def pre_sql_query(self):
        return app.data.student.pre_sql_query()

    def pre_sql_filter(self, q, filter):
        return app.data.student.pre_sql_filter(q, filter)

    def pre_sql_search(self, search):
        return app.data.student.pre_sql_search(search)

    def pre_sql_order(self, q, on, direction):
        return self.pre_sql_standard_order(q, on, direction)

    def format_data(self, l, total_count, filtered_count):
        return app.application.student.format_data(l, total_count, filtered_count)

    def show_filter_elements(self):
        return get_filters()

table_config = Config("student", "Overzicht Studenten")


@student.route('/student/sync', methods=['POST'])
@login_required
def sync_students():
    nbr_new, nbr_updated, nbr_deleted = app.application.student.student_load_from_sdh()
    ret = {"status": True, "data": {"nbr_new": nbr_new, "nbr_updated": nbr_updated, "nbr_deleted": nbr_deleted }}
    return json.dumps(ret)


