__all__ = ['tables', 'datatables', 'socketio', 'settings', 'warning', 'cron', "location", "api", "upgrade", "sms"]

from app.application.student import student_load_from_sdh


# tag, cront-task, label, help
cron_table = [
    ('SDH-STUDENT', student_load_from_sdh, 'VAN SDH, laad studenten', ''),
]

