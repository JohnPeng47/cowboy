from src.config import LOG_DIR

import logging
import os
from datetime import datetime
import pytz
import sys

def converter(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=pytz.utc)
    return dt.astimezone(pytz.timezone("US/Eastern")).timetuple()


formatter = logging.Formatter(
    "%(asctime)s - %(name)s:%(levelname)s: %(filename)s:%(lineno)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
formatter.converter = converter

def get_file_handler(log_dir=LOG_DIR, file_prefix: str = ""):
    """
    Returns a file handler for logging.
    """
    log_subdir = os.path.join(log_dir, file_prefix)
    os.makedirs(log_subdir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    file_name = f"{file_prefix}_{timestamp}.log"
    file_handler = logging.FileHandler(os.path.join(log_subdir, file_name))
    file_handler.setFormatter(formatter)
    return file_handler

def get_console_handler():
    """
    Returns a console handler for logging.
    """
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    return console_handler


def get_logfile_id(log_dir=LOG_DIR, file_prefix: str = "") -> tuple[str, int]:
    """
    Returns a tuple of (timestamp, next_id) for `file_prefix` log files.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_subdir = os.path.join(log_dir, file_prefix, timestamp)
    os.makedirs(log_subdir, exist_ok=True)
    
    existing_logs = [f for f in os.listdir(log_subdir) if f.endswith(".log")]
    next_number = 0
    if existing_logs:
        numbers = [int(f.split(".")[0]) for f in existing_logs]
        next_number = max(numbers) + 1
        
    return timestamp, next_number

def get_incremental_file_handler(log_dir=LOG_DIR, file_prefix: str = ""):
    """
    Returns a file handler that creates logs in timestamped directories with incremental filenames.
    Directory structure: log_dir/file_prefix/YYYY-MM-DD/0.log, 1.log, etc.
    """
    timestamp, next_number = get_logfile_id(log_dir, file_prefix)
    log_subdir = os.path.join(log_dir, file_prefix, timestamp)
    
    # Create new log file with incremental number
    file_name = f"{next_number}.log"
    file_handler = logging.FileHandler(os.path.join(log_subdir, file_name))
    file_handler.setFormatter(formatter)
    return file_handler

testgen_logger = logging.getLogger("testgen_logger")
testgen_logger.setLevel(logging.INFO)
testgen_logger.addHandler(get_incremental_file_handler(file_prefix="testgen"))

buildtm_logger = logging.getLogger("buildtm_logger")
buildtm_logger.setLevel(logging.INFO)
buildtm_logger.addHandler(get_file_handler(file_prefix="buildtm"))
buildtm_logger.addHandler(get_console_handler())

sync_repo = logging.getLogger("sync_repo")
sync_repo.setLevel(logging.INFO)
sync_repo.addHandler(get_file_handler(file_prefix="syncrepo"))

master_logger = logging.getLogger("master_logger")
# Add handlers from all other loggers
for logger in [testgen_logger, buildtm_logger, sync_repo]:
    for handler in logger.handlers:
        master_logger.addHandler(handler)

# Add console handler if not already present
if not any(isinstance(h, logging.StreamHandler) for h in master_logger.handlers):
    master_logger.addHandler(get_console_handler())

loggers = [testgen_logger, sync_repo, buildtm_logger, master_logger]


def set_log_level(level=logging.INFO):
    """
    Sets the logging level for all defined loggers.
    """
    for logger in loggers:
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


def configure_uvicorn_logger():
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addHandler(get_file_handler())
    uvicorn_error_logger.addHandler(get_console_handler())


# LOGFIRE METRICS
# accepted_count = logfire.metric_counter("accepted_tests", unit="1")
# failed_count = logfire.metric_counter("failed_tests", unit="1")
# total_count = logfire.metric_counter("total_tests", unit="1")
