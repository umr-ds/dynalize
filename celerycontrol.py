'''
@author: PUM
'''
import log
import traceback
import database
import task # needed for celery daemon

from celery import Celery
from udsclient import UnixDomainSocketClient
from database.model.task import Task

logger = log.setup_logger(__name__)

cel = Celery('celerycontrol')
cel.config_from_object("celery_settings")

@cel.task
def add_task_uds(task):
    ''' This will be called from the master and executed on a client '''
    client = UnixDomainSocketClient()
    try:
        logger.debug("Sending task to unix domain socket")
        client.send_json_task(task.to_json())
    except:
        logger.error(traceback.format_exc())
        return False

    return True

@cel.task
def add_task_result(task_result):
    ''' This will be called from a client and executed on the master '''
    logger.debug("Got task_result result -> adding to DB")

    try:
        # This will be called from the celery worker and not from the main module, therefore we need to make sure, that the DB is initialized
        database.setup_db()

        with database.get_session() as session:
            # T
            inst = session.query(Task).filter(Task.task_id == task_result.task_id)
            result = inst.one()

            result.completed = task_result.completed
            result.output = task_result.output
            result.build_logs = ''.join(task_result.build_logs)
            result.exception = task_result.exception
            result.traceback = task_result.traceback
            result.worker_hostname = task_result.hostname
            result.exit_code = task_result.exit_code
            result.duration = task_result.duration

            session.commit()
    except:
        logger.error(traceback.format_exc())
        return False

    return True

def revoke_task(backend_task_id):
    try:
        cel.control.revoke(backend_task_id)
    except:
        logger.error(traceback.format_exc())
        return False

    return True

def get_running_worker():
    result = set()

    try:
        stats = cel.control.inspect().stats()

        if stats is not None:
            for k, v in stats.items():
                # If the key contains an '@' use the string after the '@' as the hostname
                # otherwise use value.broker.hostname, but this might result in getting the ip instead of the hostname!
                if "@" in k:
                    result |= {k.split('@')[1]}
                else:
                    result |= {v['broker']['hostname']}
    except:
        pass

    return result
