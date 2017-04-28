'''
@author: PUM
'''
import os
import log
import config
import atexit
import concurrent.futures
import shutil

logger = log.setup_logger(__name__)

_workerpool = None

_cache_dir_name = "cache"
_tasks_dir_name = "tasks"
_input_basedir_name = "input"
_output_basedir_name = "output"

def setup_cacher():
    global _workerpool

    cache_path = get_cache_path()
    tasks_path = os.path.join(config.cacher_directory, _tasks_dir_name)

    if not os.path.exists(cache_path):
        logger.debug("Cacher directory '%s' does not exist -> creating." % config.cacher_directory)
        # makedirs will make sure to create all directories if they not exist up to the last one
        # therefore appending the cache-directory will make sure we get the directory specified in config.cacher_directory and the cache directory
        os.makedirs(cache_path, exist_ok=True)
    else:
        if config.cacher_empty_cache:
            shutil.rmtree(cache_path, ignore_errors=True)

            # rmtree not only deletes files under the cache/ directory but the cache directory itself
            # therefore this one needs be recreated afterwards
            os.makedirs(cache_path)

    # Make sure old files/folders for the tasks are deleted
    shutil.rmtree(tasks_path, ignore_errors=True)
    os.makedirs(tasks_path, exist_ok=True)

    _workerpool = concurrent.futures.ThreadPoolExecutor(max_workers=config.cacher_threads)


def add_task(task, *args, **kwargs):
    return _workerpool.submit(task, *args, **kwargs)

def prepare_cache(task_id):
    ''' Creates input- and output-directory for the passed task_id and returns the relative paths to each as a tuple '''
    input_path = os.path.join(config.cacher_directory, _tasks_dir_name, task_id, _input_basedir_name)
    output_path = os.path.join(config.cacher_directory, _tasks_dir_name, task_id, _output_basedir_name)
    base_path = os.path.join(config.cacher_directory, _tasks_dir_name, task_id)

    os.makedirs(input_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    # As the cacher directory is auto-prepended, we only return the subfolders here
    return input_path, output_path, base_path

def get_cache_path():
    return os.path.join(config.cacher_directory, _cache_dir_name)

@atexit.register
def stop_cacher():
    # Make sure all workers terminate, although this should work out-of-the-box in most cases
    if _workerpool is not None:
        _workerpool.shutdown()
