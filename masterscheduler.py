'''
@author: PUM
'''
import log
import re
import traceback
import task
import database.model
import celerycontrol
import config

from database.model.job import Job
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from data_providers.basedataprovider import BaseDataProvider
from database.model.task import Task
from master_api.v1.layer import _get_layer_tree


logger = log.setup_logger(__name__)

source_path_re = re.compile("{{source_path}}", re.IGNORECASE)
source_file_re = re.compile("{{source_filename}}", re.IGNORECASE)

class MasterScheduler():
    def __init__(self):
        pass

    def add_job(self, job_id):
        logger.debug("Got Job '%s' -> schedule it" % job_id)

        database.setup_db()

        with database.get_session() as session:
            try:
                job_data = session.query(Job).filter(Job.job_id == job_id).one()
                cloud_data = job_data.clouddef

                if job_data.source_datadef_id is None or job_data.destination_datadef_id is None:
                    raise ValueError("Missing dataprovider information")

                if job_data.run_layer_id is None:
                    raise ValueError("Missing run layer")

                if job_data.script_id is None:
                    raise ValueError("Missing script")

                source_dp_data = job_data.source_datadef_relation
                destination_dp_data = job_data.destination_datadef_relation

                source_dp, source_dp_kwargs = BaseDataProvider.dataprovider_by_model(source_dp_data)
                destination_dp, destiantion_dp_kwargs = BaseDataProvider.dataprovider_by_model(destination_dp_data)

                # We only need to instantiate the source data provider, as only the settings of the destination data provider are relevant here.
                # A destination data provider instance is needed on the corresponding task worker
                source_dp = source_dp(**source_dp_kwargs)
                source_files = source_dp.get_files(source_dp_data.source)

                # Check for a path filter and return only files with a path matching the filter
                if source_dp_data.source_path_filter is not None and len(source_dp_data.source_path_filter) > 0:
                    source_filter = re.compile(source_dp_data.source_path_filter)
                    source_files = [x for x in source_files if source_filter.search(x.path)]

                # Check for a filename filter and return only files matching the filter
                if source_dp_data.source_filename_filter is not None and len(source_dp_data.source_filename_filter) > 0:
                    source_filter = re.compile(source_dp_data.source_filename_filter)
                    source_files = [x for x in source_files if source_filter.search(x.filename)]

                running_worker = celerycontrol.get_running_worker()

                for f in source_files:
                    task_name = (job_data.name or job_data.job_id) + " - " + f.filename

                    logger.debug("Sourcefile (path='%s', filename='%s') received -> generating task '%s'" % (f.path, f.filename, task_name))

                    task_destination_path = source_path_re.sub(f.path, destination_dp_data.destination)
                    task_destination_path = source_file_re.sub(f.filename, task_destination_path)

                    logger.debug("Destination path created. Org='%s', created='%s'" % (destination_dp_data.destination, task_destination_path))

                    task_source_dp = task.TaskDataProvider(source_dp_data.dataprovider_relation.name, f.fullpath, None, source_dp_kwargs)
                    logger.debug("Created source data provider. Type='%s', source='%s'" % (source_dp_data.dataprovider_relation.name, f.fullpath))

                    task_destination_dp = task.TaskDataProvider(destination_dp_data.dataprovider_relation.name, None, task_destination_path, destiantion_dp_kwargs)
                    logger.debug("Created destination data provider. Type='%s', destination='%s'" % (destination_dp_data.dataprovider_relation.name, task_destination_path))

                    virtual_device_layer_content = '\n'.join([l.content for l in _get_layer_tree(cloud_data.virtual_device_layer_relation.layer_id)])
                    test_layer_content = '\n'.join([l.content for l in _get_layer_tree(cloud_data.test_layer_relation.layer_id)])
                    run_layer_content = '\n'.join([l.content for l in _get_layer_tree(cloud_data.run_layer_relation.layer_id)])

                    task_virtual_device_layer = task.TaskLayer(virtual_device_layer_content, cloud_data.virtual_device_layer_relation.tag)
                    task_test_layer = task.TaskLayer(test_layer_content, cloud_data.test_layer_relation.tag)
                    task_run_layer = task.TaskLayer(run_layer_content, job_data.run_relation.tag)
                    task_script = task.TaskScript(job_data.script_relation.content, job_data.script_relation.name)

                    task_filename = f.filename

                    logger.debug("Adding task to internal database")
                    database_task = database.model.task.Task(
                                                        job_id = job_data.job_id,
                                                        filename = task_filename,
                                                        completed = False
                                                        )

                    session.add(database_task)
                    session.commit()

                    logger.debug("Task added to database with id='%s'" % database_task.task_id)

                    new_task = task.Task(database_task.task_id, task_name, task_source_dp, task_destination_dp, task_virtual_device_layer, task_test_layer, task_run_layer, task_script, task_filename, job_data.task_timeout)

                    celery_queue = None

                    if config.master_scheduling_algo == "history":
                        # Look for a worker which previously executed a task with the same filename
                        task_hist = session.query(Task).join(Job).filter(Job.clouddef_id == cloud_data.clouddef_id, Task.filename == task_filename).all()

                        for row in task_hist:
                            if row.worker_hostname is not None and row.worker_hostname in running_worker:
                                # We found a worker which is running, executed the same file in the past and probably still has the file in its local cache
                                celery_queue = "worker-" + row.worker_hostname
                                break

                    # Fallback in case no worker was found or another schedule algo was specified
                    if celery_queue is None:
                        celery_queue = "cloud-" + str(cloud_data.clouddef_id)

                    try:
                        celery_task = celerycontrol.add_task_uds.apply_async((new_task,), queue=celery_queue)  # @UndefinedVariable
                    except Exception as exc:
                        logger.error(traceback.format_exc())
                        database_task.exception = str(exc)
                        database_task.traceback = traceback.format_exc()
                        database_task.completed = True

                    logger.debug("Task submitted to celery queue '%s' with id='%s'" % (celery_queue, celery_task.id))

                    # Add the backend id (in this case the celery id) to the database
                    database_task.backend_id = celery_task.id
                    session.commit()
            except (MultipleResultsFound, NoResultFound):
                raise ValueError("Received unknown or invalid job id")

    def remove_job(self, job_id):
        # TODO: Similar to remove_task?
        pass

    def remove_task(self, task_id):
        with database.get_session() as session:
            try:
                task_data = session.query(Task).filter(Task.task_id == task_id).one()

                if task_data.backend_id is not None and not task_data.completed:
                    # Make sure the task is revoked on celery if its not completed yet
                    celerycontrol.revoke_task(task_data.backend_id)

                session.delete(task_data)
                session.commit()
            except (MultipleResultsFound, NoResultFound):
                raise ValueError("Received unknown or invalid job id")
