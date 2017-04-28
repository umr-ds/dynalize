'''
@author: PUM
'''
import console as Con
import config
import log
import master_api
import database
import cacher
import atexit
import sys
import socket
import os

from clientscheduler import ClientScheduler
from udsserver import UnixDomainSocketServer
from celerytaskconsumer import CeleryTaskConsumer
from subprocess import Popen
from deployment import manual_s3_deployment

logger = log.setup_logger(__name__)
process = None

@atexit.register
def kill_process():
    if process is not None:
        process.kill()

def demote(user_uid, user_gid):
    def result():
        if os.name == 'posix':
            os.setgid(user_gid)  # @UndefinedVariable
            os.setuid(user_uid)  # @UndefinedVariable
    return result

def get_user_demote():
    if os.name == 'posix':
        import pwd  # @UnresolvedImport
        pw_record = pwd.getpwnam(config.client_username)

        return demote(pw_record.pw_uid, pw_record.pw_gid)

    return None

def start_master():
    logger.debug("Launching master daemon")
    database.setup_db()
    database.create_schema()

    if config.insert_inital_data:
        database.insert_initial_data()

    # Start celery worker to consume results
    fn = get_user_demote()
    if fn is None:
        process = Popen(["celery", "worker", "--app=celerycontrol", "-l" , "info", "-Q", "results"])
    else:
        process = Popen(["celery", "worker", "--app=celerycontrol", "-l" , "info", "-Q", "results"], preexec_fn=fn)

    master_api.setup.run()

def start_worker():
    logger.debug("Launching client daemon")

    # Make sure cacher is ready
    cacher.setup.setup_cacher()

    # Start the client scheduler
    scheduler = ClientScheduler()

    if scheduler.is_running():
        # Starting CeleryTaskConsumer to consume each finished task and report back to master
        logger.debug("Starting celery task consumer")
        CeleryTaskConsumer(scheduler)

        # Start celery worker with specified queue and add queue for the hostname
        worker_queue = "worker-" + socket.gethostname()

        if len(config.client_queues) > 0:
            config.client_queues += "," + worker_queue
        else:
            config.client_queues = worker_queue

        logger.debug("Starting celery worker with queues '%s'" % config.client_queues)
        fn = get_user_demote()
        if fn is None:
            process = Popen(["celery", "worker", "--app=celerycontrol", "-l" , "info", "-Q", config.client_queues])
        else:
            process = Popen(["celery", "worker", "--app=celerycontrol", "-l" , "info", "-Q", config.client_queues], preexec_fn=fn)

        # Starting UnixDomainSocketServer as a task producer for our scheduler
        logger.debug("Starting unix domain socket server")
        UnixDomainSocketServer(scheduler)


if __name__ == '__main__':
    # Read commandline arguments and setup_db config
    Con.setup_console()

    if config.s3_deployment:
        manual_s3_deployment()
        sys.exit()

    if config.master_daemon:
        start_master()
    else:
        start_worker()
