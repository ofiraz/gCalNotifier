import logging
from logging.handlers import RotatingFileHandler

# Logger log levels
LOG_LEVEL_CRITICAL = 50
LOG_LEVEL_ERROR = 40
LOG_LEVEL_WARNING = 30
LOG_LEVEL_INFO = 20
LOG_LEVEL_DEBUG = 10
LOG_LEVEL_NOTSET = 0

def init_logging(module_name, process_name, file_log_level, start_message_log_level):
    # create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s - %(lineno)d - ' + process_name + ' - %(process)d - (%(threadName)-10s) - %(levelname)s - %(message)s')

    # create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # add formatter to ch
    console_handler.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(console_handler)

    # Create file handler
    log_file = module_name + ".log"
    max_log_file_size = 100 * 1024 * 1024
    file_handler = RotatingFileHandler(
        log_file,
        mode='a',
        maxBytes=max_log_file_size,
        backupCount=5,
        encoding='utf-8')

    file_handler.setLevel(file_log_level)

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.log(start_message_log_level, "========")
    logger.log(start_message_log_level, "Starting")
    logger.log(start_message_log_level, "========")

    return logger
