__all__ = ['tables', 'datatables', 'socketio', 'settings', 'warning', 'wisa', 'cron', 'cardpresso', 'photo', 'student', 'ad', 'test', 'staff', "azure", "location"]


from app.application.photo import cron_task_photo
from app.application.wisa import cron_task_wisa_get_student
from app.application.wisa import cront_task_wisa_get_staff
from app.application.cardpresso import cron_task_new_badges
from app.application.cardpresso import cron_task_new_rfid_to_database
from app.application.ad import student_process_flagged, staff_process_flagged, student_cron_task_get_computer
from app.application.staff import staff_post_processing

from app.application.student import student_load_from_sdh


# tag, cront-task, label, help
cron_table = [
    ('SDH-STUDENT', student_load_from_sdh, 'VAN SDH, laad studenten', ''),
]

import app.application.azure