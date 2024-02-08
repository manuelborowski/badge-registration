from app import flask_app
import os, sys

#logging on file level
import logging
from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


def get_upgrade_files(versions):
    try:
        versions = versions.split("-")
        first_version = float(versions[0])
        last_version = float(versions[1])
        log.info(f"{sys._getframe().f_code.co_name}: get version from {first_version} till {last_version}")
        upgrade_path = os.path.join(flask_app.static_folder, "upgrade")
        files = os.listdir(upgrade_path)
        all_prefixes = [float(s.split("-")[0]) for s in files if "-" in s]
        versions = [p for p in all_prefixes if p >= first_version and p <= last_version]
        update_files = []
        for version in versions:
            entry = {}
            if f"{version}-update.sql" in files:
                content = open(f"{upgrade_path}/{version}-update.sql", "r").read()
                entry["sql"]= content
            elif f"{version}-config.py" in files:
                content = open(f"{upgrade_path}/{version}-config.py", "r").read()
                entry["config"] = content
            elif f"{version}-bash.sh" in files:
                content = open(f"{upgrade_path}/{version}-bash.sh", "r").read()
                entry["shell"] = content
            if entry:
                entry["version"] = version
                update_files.append(entry)
        if "bash.sh" in files:
            content = open(f"{upgrade_path}/bash.sh", "r").read()
            update_files.append(({"shell": content}))
        return update_files
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return []

