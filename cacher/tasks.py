'''
@author: PUM
'''
import log
import traceback

logger = log.setup_logger(__name__)

class CacherTask():
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        logger.debug("Start CacherTask <func: '%s', args: '%s', kwargs: '%s'>" % (self.func, self.args, self.kwargs))
        try:
            self.func(*self.args, **self.kwargs)
        except Exception:
            logger.error(traceback.format_exc())

        logger.debug("End CacherTask <func: '%s', args: '%s', kwargs: '%s'>" % (self.func, self.args, self.kwargs))
