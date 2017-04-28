'''
Created on 02.04.2015

@author: PUM
'''
import celerycontrol
import log
import traceback

from threading import Thread

logger = log.setup_logger(__name__)

class CeleryTaskConsumer():
    def __init__(self, scheduler):
        '''        Constructor        '''
        self.scheduler = scheduler

        self.run()

    def run(self):
        self.queue_thread = Thread(target=self.queue_consumer)
        # Make sure this thread prevents the exit of the whole application
        self.queue_thread.daemon = False
        self.queue_thread.start()

    def queue_consumer(self):
        while True:
            finished_task = self.scheduler.task_results.get()

            logger.debug("Got finished task '%s', adding to celery result queue" % finished_task)

            try:
                celerycontrol.add_task_result.apply_async((finished_task,))  # @UndefinedVariable
            except:
                logger.error(traceback.format_exc())
                logger.error("Failed to add finished task to result-task-queue in celery.")
