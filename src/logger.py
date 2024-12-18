from src.config import LOG_DIR

import logging
import os
from datetime import datetime
import pytz
import sys

import logging
from typing import List, Union

class MultiLogger:
    """
    A class that wraps multiple loggers and propagates log messages to all of them.
    Exposes standard logging methods (debug, info, warning, error, critical).
    """
    
    def __init__(self, *loggers: logging.Logger):
        """
        Initialize MultiLogger with one or more logging.Logger instances.
        
        Args:
            *loggers: Variable number of logging.Logger instances
        """
        if not loggers:
            raise ValueError("At least one logger must be provided")
            
        self.loggers = loggers
        
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message to all loggers."""
        for logger in self.loggers:
            logger.debug(msg, *args, **kwargs)
            
    def info(self, msg: str, *args, **kwargs):
        """Log info message to all loggers."""
        for logger in self.loggers:
            logger.info(msg, *args, **kwargs)
            
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message to all loggers."""
        for logger in self.loggers:
            logger.warning(msg, *args, **kwargs)
            
    def error(self, msg: str, *args, **kwargs):
        """Log error message to all loggers."""
        for logger in self.loggers:
            logger.error(msg, *args, **kwargs)
            
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message to all loggers."""
        for logger in self.loggers:
            logger.critical(msg, *args, **kwargs)
            
    def exception(self, msg: str, *args, exc_info=True, **kwargs):
        """Log exception message to all loggers."""
        for logger in self.loggers:
            logger.exception(msg, *args, exc_info=exc_info, **kwargs)
            
    def log(self, level: int, msg: str, *args, **kwargs):
        """Log message with specified level to all loggers."""
        for logger in self.loggers:
            logger.log(level, msg, *args, **kwargs)
            
    def setLevel(self, level: Union[int, str]):
        """Set logging level for all loggers."""
        for logger in self.loggers:
            logger.setLevel(level)
            
    def isEnabledFor(self, level: int) -> bool:
        """
        Check if any logger is enabled for specified level.
        Returns True if at least one logger is enabled for the level.
        """
        return any(logger.isEnabledFor(level) for logger in self.loggers)

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
    Also checks for empty log files and removes them, renaming subsequent files 
    to maintain sequential numbering. For example, if 0.log is empty and 1.log exists,
    1.log will be renamed to 0.log before returning the next available ID.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_subdir = os.path.join(log_dir, file_prefix, timestamp)
    os.makedirs(log_subdir, exist_ok=True)
    
    existing_logs = [f for f in os.listdir(log_subdir) if f.endswith(".log")]
    existing_logs.sort(key=lambda x: int(x.split(".")[0]))
    
    # Check for and remove empty files, shifting other files down
    current_index = 0
    for log_file in existing_logs:
        file_path = os.path.join(log_subdir, log_file)
        if os.path.getsize(file_path) == 0:
            os.remove(file_path)
            continue
            
        # Rename file if its index doesn't match current_index
        expected_name = f"{current_index}.log"
        if log_file != expected_name:
            os.rename(
                file_path,
                os.path.join(log_subdir, expected_name)
            )
        current_index += 1
    
    return timestamp, current_index

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

# master_logger = logging.getLogger("master_logger")
# # Add handlers from all other loggers
# for logger in [testgen_logger, buildtm_logger, sync_repo]:
#     for handler in logger.handlers:
#         master_logger.addHandler(handler)

# # Add console handler if not already present
# if not any(isinstance(h, logging.StreamHandler) for h in master_logger.handlers):
#     master_logger.addHandler(get_console_handler())

loggers = [testgen_logger, sync_repo, buildtm_logger]

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
