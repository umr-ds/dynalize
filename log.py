import logging
import config
from logging import NOTSET

class WebSocketLogger(logging.Handler):
    def __init__(self, level=NOTSET):
        logging.Handler.__init__(self, level=level)
        self.websocket_root = None

    def set_websocket_root(self, websocket_root):
        self.websocket_root = websocket_root

    def emit(self, record):
        if self.websocket_root is None:
            return

        try:
            msg = self.format(record)

            self.websocket_root.notify(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

log_observer = WebSocketLogger()

def setup_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    log_observer.setFormatter(formatter)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)

    if config.debug:
        logger.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    logger.addHandler(log_observer)
    return logger
