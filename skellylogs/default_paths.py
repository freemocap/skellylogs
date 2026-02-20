import time
from datetime import datetime
from pathlib import Path

DEFAULT_SKELLYLOGS_BASE_FOLDER_NAME = "skellylogs_data"
LOGS_FOLDER_NAME = "logs"


def _get_base_folder_path() -> Path:
    return Path.home() / DEFAULT_SKELLYLOGS_BASE_FOLDER_NAME


def _get_gmt_offset_string() -> str:
    gmt_offset_int = int(time.localtime().tm_gmtoff / 60 / 60)
    return f"{gmt_offset_int:+}"


def _get_iso8601_time_string(
    timespec: str = "milliseconds",
    filename_friendly: bool = True,
) -> str:
    timestamp = datetime.now().isoformat(timespec=timespec)
    gmt_offset = f"_gmt{_get_gmt_offset_string()}"
    result = timestamp + gmt_offset
    if filename_friendly:
        result = result.replace(":", "_").replace(".", "ms")
    return result


def _create_log_file_name() -> str:
    return f"log_{_get_iso8601_time_string()}.log"


def get_log_file_path() -> str:
    """Return the default log file path, creating the directory if needed.

    Logs are written to ~/skellylogs_data/logs/<iso8601_timestamp>.log.
    """
    log_folder = _get_base_folder_path() / LOGS_FOLDER_NAME
    log_folder.mkdir(exist_ok=True, parents=True)
    return str(log_folder / _create_log_file_name())
