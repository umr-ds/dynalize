'''
@author: PUM
'''
import concurrent.futures
import config
import log
import dockermanager
import traceback
import os
import time

from queue import Queue
from threading import Thread
from task import Task, TaskResult
from dockermanager import DockerVolume
from data_providers.basedataprovider import BaseDataProvider
from cacher.cachemanager import CacheManager
import app_exceptions

logger = log.setup_logger(__name__)

class ClientScheduler():

    def __init__(self):
        self.waiting_tasks = Queue()
        self.task_results = Queue()

        self._workerpool = concurrent.futures.ThreadPoolExecutor(max_workers=config.client_threads)

        self.manager = dockermanager.DockerManager(config.client_docker_url)

        try:
            self.manager.is_working()
        except:
            logger.error("Can't connect to docker -> stopping.")
            logger.error(traceback.format_exc())
            return

        # If a deployment file exists, we build the layers and stop afterwards
        if self.check_deployment():
            return

        self.run()

    def is_running(self):
        try:
            return self.queue_thread.is_alive()
        except:
            return False

    def run(self):
        self.queue_thread = Thread(target=self.queue_worker)
        # Make sure this thread prevents the exit of the whole application
        self.queue_thread.daemon = False
        self.queue_thread.start()

    def check_deployment(self):
        if os.path.isfile("deploy.json"):
            logger.debug("Found deploy.json file -> Running deployment")

            with open("deploy.json", "rb") as f:
                json_str = f.read().decode("utf-8")

            logger.debug("deploy.json: %s" % json_str)

            task = Task.from_json_deployment(json_str)

            virtual_device_layer_id, test_layer_id, build_logs = self.build_main_layers(task)

            logger.debug("Deployment complete. Removing deploy.json now.")
            logger.debug("Built virtual-device-layer with id '%s'" % virtual_device_layer_id)
            logger.debug("Built test-layer with id '%s'" % test_layer_id)
            logger.debug("Build Logs: %s" % build_logs)

            os.remove("deploy.json")

            return True

    def queue_worker(self):
        while True:
            task = self.waiting_tasks.get()

            logger.debug("Got Task '%s' ('%s') -> schedule it" % (task.name, task.task_id))

            fut = self._workerpool.submit(self.task_worker, task)

            # Make sure we create a copy of task, as python uses late binding of closures!
            def finish_task(f, task=task):
                task_result = f.result()

                logger.debug("Task '%s' ('%s') finished" % (task.name, task.task_id))
                logger.debug("Task '%s' ('%s') log: %s" % (task.name, task.task_id, task_result.output))
                logger.debug("Task '%s' ('%s') exception: %s" % (task.name, task.task_id, task_result.exception))

                self.task_results.put(task_result)

            fut.add_done_callback(finish_task)


    def build_main_layers(self, task, task_result):
        # Check if test_layer is available
        if not self.manager.is_image_available(task.virtual_device_layer['tag']):
            logger.warn("Virtual device layer '%s' for Task '%s' is not available on this system. Building might take some time." % (task.virtual_device_layer['tag'], task.task_id))

        virtual_device_layer_id, virtual_device_layer_log = self.manager.build_with_cache(task.virtual_device_layer['content'], task.virtual_device_layer['tag'])
        task_result.build_logs.extend(virtual_device_layer_log)

        if not self.manager.is_image_available(task.test_layer['tag']):
            logger.warn("Test layer '%s' for Task '%s' is not available on this system. Building might take some time." % (task.test_layer['tag'], task.task_id))

        if virtual_device_layer_id is not None:
            # Make sure test layer is based upon virtual device layer!
            test_layer_content = "FROM " + virtual_device_layer_id + "\n" + task.test_layer['content']
            test_layer_id, test_layer_log = self.manager.build_with_cache(test_layer_content, task.test_layer['tag'])
            task_result.build_logs.extend(test_layer_log)
        else:
            raise app_exceptions.DockerBuildException("Virtual device layer id is missing (maybe virtual device layer failed to build?). Can't continue building test layer.")

        return virtual_device_layer_id, test_layer_id

    def task_worker(self, task):
        task_result = TaskResult(task.task_id)
        lst_futures = []

        start_time = time.time()

        try:
            # Make sure all main layers are up-to-date!
            _, test_layer_id = self.build_main_layers(task, task_result)

            # Build Runlayer (Use a cache dictionary to prevent unnecessary build attempts)
            run_layer_content = "FROM " + test_layer_id + "\n" + task.run_layer['content']
            run_layer_id, run_layer_log = self.manager.build_with_cache(run_layer_content, task.run_layer['tag'])

            task_result.build_logs.extend(run_layer_log)

            # Prepare Cache
            cache = CacheManager(task.task_id)

            # Write test script into input cache
            cache.write_script(task.script['content'])

            # Start container (usually needs more time than the cache)
            input_volume = DockerVolume(cache.input_path, "/mnt/input/", readonly=True)
            output_volume = DockerVolume(cache.output_path, "/mnt/output/", readonly=False)

            env = {
                   'TASK_NAME' : task.name,
                   'TASK_ID' : task.task_id,
                   'TASK_FILE' : task.task_file,
                   'TASK_INPUT_PATH' : "/mnt/input/",
                   'TASK_OUTPUT_PATH' : "/mnt/output/"
                   }

            try:
                cont = self.manager.run(run_layer_id, env_dict=env, volumelist=[input_volume, output_volume])
            except:
                cont = self.manager.run(run_layer_id, env_dict=env)

            # Start Cache download
            source_data_provider = BaseDataProvider.dataprovider_by_name(task.source_data_def['data_provider_type'])
            fut_cache_start = cache.add_download_task(source_data_provider, task.source_data_def['source'], task.task_file, **task.source_data_def['kwargs'])
            lst_futures.append(fut_cache_start)

            # Wait for Cache download complete & signal to container
            def cache_complete(f, cont=cont):
                # Create a input-file indicating that the cache is ready
                open(os.path.join(cache.input_path, "data_ready"), "a").close()

            fut_cache_start.add_done_callback(cache_complete)

            # Wait for container exit
            task_result.exit_code = cont.wait_until_stopped(task.timeout)

            if cont.is_running():
                logger.warn("Killing container '%s' as we reached the timeout for task '%s'" % (cont.get_id(), task.task_id))
                cont.stop()

            # Make sure the output are a string to allow serialization
            task_result.output = cont.output().decode("utf-8")

            # Upload results to dataprovider
            destination_data_provider = BaseDataProvider.dataprovider_by_name(task.destination_data_def['data_provider_type'])
            lst_futures.extend(cache.upload_output_files(destination_data_provider, task.destination_data_def['destination'], **task.destination_data_def['kwargs']))

            task_result.completed = True
        except Exception as exc:
            logger.error(traceback.format_exc())
            task_result.exception = str(exc)
            task_result.traceback = traceback.format_exc()
        finally:
            # Try to remove the container
            cont.remove()

            # Use a thread here to cleanup cache after all downloads/upload-tasks are complete
            def cache_cleanup_thread(lst_futures=lst_futures, cache=cache, task_result=task_result):
                #TODO: Check for future.exception and send them to the master
                concurrent.futures.wait(lst_futures)
                cache.cleanup()

            # TODO: Use a (global) threadpool here for better resource utilization?
            cleanup_thread = Thread(target=cache_cleanup_thread)
            cleanup_thread.start()

        task_result.duration = time.time() - start_time
        return task_result


    def add_task(self, task):
        self.waiting_tasks.put(task)

    def add_task_from_json(self, json):
        new_task = Task.from_json(json)
        self.add_task(new_task)
