import os
import traceback
from logging import basicConfig
from logging import ERROR
from logging import getLevelName
from logging import getLogger
from logging import Logger
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

import dca_investment_bot.global_vars as global_vars
from dca_investment_bot.paths import Paths

# TODO: Figure out why Optional[Logger] doesnt work here with mypy
logger: Logger = None  # type: ignore
logger_initialized = False


def init_logger(log_level: str, log_file: str):
    global logger, logger_initialized

    if len(log_file) == 0:
        print("[LOGGER]", "Log file not set, using default")
        log_file = Paths.default_log_filename

    # Set default log settings
    cwd = os.getcwd()
    log_dir = Paths.logs_directory
    log_path = os.path.join(cwd, log_dir, log_file)

    # create logging directory
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    file_handler = TimedRotatingFileHandler(log_path, when="midnight")
    basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[file_handler, StreamHandler()],
    )
    logger = getLogger(__name__)

    # make sure log_level is valid ( DEBUG, INFO, WARNING, ERROR, CRITICAL)
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        logger.log(ERROR, "Invalid log level specified. Defaulting to INFO")
        LOG_ERROR(f"ERROR: Invalid log level: {log_level}", "Defaulting to INFO")
        log_level = getLevelName("INFO")

    level = getLevelName(log_level)
    logger.setLevel(level)
    logger_initialized = True


def __concat_args(*args):
    # concate all args to one string
    log_string = ""
    for arg in args:
        log_string += str(arg) + " "
    return log_string


def log_to_error_file(*args):
    # try logging but if that doesnt work, try printing the exception
    try:
        with open(Paths.uninitialized_logger_error_file_path, "a") as f:
            f.write(__concat_args(*args) + "\n")
            print(__concat_args(*args))
    except Exception as ex:
        print("[LOGGER]", "Error writing to error.log")
        print(ex)
        print(traceback.format_exc())


def LOG_INFO(*args):
    if not logger_initialized:
        log_to_error_file(*args)
    else:
        logger.info(__concat_args(*args))


def LOG_ERROR(*args):
    if not logger_initialized:
        log_to_error_file(*args)
    else:
        logger.error(__concat_args(*args))


def LOG_ERROR_AND_NOTIFY(*args):
    LOG_ERROR(*args)
    if global_vars.firebaseMessager is not None:
        global_vars.firebaseMessager.push_notification("Error!", __concat_args(*args))


def LOG_WARNING(*args):
    if not logger_initialized:
        log_to_error_file(*args)
    else:
        logger.warning(__concat_args(*args))


# TODO: Move this into a external function to keep the code clean from dependencies
def LOG_WARNING_AND_NOTIFY(*args):
    LOG_WARNING(*args)
    if global_vars.firebaseMessager is not None:
        global_vars.firebaseMessager.push_notification("Warning!", __concat_args(*args))


def LOG_DEBUG(*args):
    if not logger_initialized:
        log_to_error_file(*args)
    else:
        logger.debug(__concat_args(*args))


def LOG_CRITICAL(*args):
    if not logger_initialized:
        log_to_error_file(*args)
    else:
        logger.critical(__concat_args(*args))


def LOG_CRITICAL_AND_NOTIFY(*args):
    LOG_CRITICAL(*args)
    if global_vars.firebaseMessager is not None:
        global_vars.firebaseMessager.push_notification("Warning!", __concat_args(*args))


def log_and_raise_exeption(e: Exception, debug_tag: str = "[Exception]", raise_exception: bool = True):
    # try logging but if that doesnt work, try printing the exception
    exception = e
    excepton_info = traceback.format_exc()
    try:
        LOG_ERROR_AND_NOTIFY(debug_tag, e)
        LOG_ERROR_AND_NOTIFY(debug_tag, traceback.format_exc())
    except Exception as ex:
        print(debug_tag, "Initial exception that was raised:")
        print(debug_tag, e)
        print(debug_tag, excepton_info)

        print(
            debug_tag,
            "Another exception was raised during logging of the first exception:",
        )
        print(debug_tag, ex)
        print(debug_tag, traceback.format_exc())
    if raise_exception:
        raise exception
