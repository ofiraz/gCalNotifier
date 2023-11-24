from config import app_config

from logging_module import (
    init_logging,
    LOG_LEVEL_INFO,
)

class app_globals:
    def __init__(self):
        self.config = app_config()

        self.logger = init_logging("gCalNotifier", "Main", self.config.log_level, LOG_LEVEL_INFO)
        self.events_logger = init_logging("EventsLog", "Main", LOG_LEVEL_INFO, LOG_LEVEL_INFO)



