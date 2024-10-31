__all__ = ['tables', 'datatables', 'socketio', 'settings', 'warning', 'cron', "location", "api", "upgrade", "sms", "staff"]

from app.application.student import student_load_from_sdh, push_reservations_to_server
from app.application.staff import staff_load_from_sdh


# tag, cront-task, label, help
cron_table = [
    ('SDH-STUDENT-UPDATE', push_reservations_to_server, 'NAAR SDH, update studenten', ''),
    ('SDH-STUDENT', student_load_from_sdh, 'VAN SDH, laad studenten', ''),
    ('SDH-STAFF', staff_load_from_sdh, 'VAN SDH, laad personeelsleden', ''),
]

