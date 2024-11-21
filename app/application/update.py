import os, sys, yaml
from pathlib import Path

#logging on file level
import logging

from app import MyLogFilter, top_log_handle
log = logging.getLogger(f"{top_log_handle}.{__name__}")
log.addFilter(MyLogFilter())


# badge-registration version (0.69) is decoupled from update version (0.1)
# updates are grouped in a yaml file and the name is the update version (0.1.yaml)

def get_update_data(versions):
    try:
        versions = versions.split("-")
        first_version = float(versions[0])
        last_version = float(versions[1])
        log.info(f"{sys._getframe().f_code.co_name}: get version from {first_version} till {last_version}")
        update_path = "update"
        filenames = os.listdir(update_path)
        files2version = [float(Path(s).stem) for s in filenames if "yaml" in s]
        file_versions = [p for p in files2version if p >= first_version and p <= last_version]
        updates = []
        for version in file_versions:
            content = open(f"{update_path}/{version}.yaml", "r").read()
            data = yaml.safe_load(content)
            data["version"] = version
            updates.append(data)
        return {"status": True, "data": updates}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}


def get_latest_update_version():
    try:
        update_path = "update"
        filenames = os.listdir(update_path)
        files2version = sorted([float(Path(s).stem) for s in filenames if "yaml" in s])
        if len(files2version) == 0:
            latest_version = "0.0"
        else:
            latest_version = files2version[-1]
        log.info(f"{sys._getframe().f_code.co_name}: latest version: {latest_version}")
        return {"status": True, "data": latest_version}
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return {"status": False, "data": str(e)}
