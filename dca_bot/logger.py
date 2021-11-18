import os
import logging as log
from logging.handlers import TimedRotatingFileHandler
import json

# loads local configuration
config_filepath = os.path.join('configs', 'config.json')
config = None
with open(config_filepath) as config_file:
    config = json.load(config_file)

# Get logging variables
log_file = config['LOGGING']['LOG_FILE']
log_level = config['LOGGING']['LOG_LEVEL']

# Set default log settings
cwd = os.getcwd()
log_dir = "logs"
log_file = 'bot.log'
log_path = os.path.join(cwd, log_dir, log_file)

# create logging directory
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

file_handler = TimedRotatingFileHandler(log_path, when="midnight")
log.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                handlers=[file_handler, log.StreamHandler()])
logger = log.getLogger(__name__)

# make sure log_level is valid ( DEBUG, INFO, WARNING, ERROR, CRITICAL)
if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    logger.log(log.ERROR, "Invalid log level specified. Defaulting to INFO")
    print('ERROR: Invalid log level: {}'.format(log_level), "Defaulting to INFO")
    log_level = log.getLevelName('INFO')

level = log.getLevelName(log_level)
logger.setLevel(level)

def __concat_args(*args):
    # concate all args to one string
    log_string = ''
    for arg in args:
        log_string += str(arg) + ' '
    return log_string

def LOG_INFO(*args):
    logger.info(__concat_args(*args))

def LOG_ERROR(*args):
    logger.error(__concat_args(*args))

def LOG_WARNING(*args):
    logger.warning(__concat_args(*args))

def LOG_DEBUG(*args):
    logger.debug(__concat_args(*args))

def LOG_CRITICAL(*args):
    logger.critical(__concat_args(*args))

