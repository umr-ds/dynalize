'''
@author: PUM
'''
import cacher
import os
import shutil
import log
import traceback

logger = log.setup_logger(__name__)

_user_libs_dirname = "user_libs"

class CacheManager():
    ''' Creates a cache manager, specific for one task '''

    def __init__(self, task_id):
        '''        Constructor        '''
        self.task_id = str(task_id)
        self.input_path, self.output_path, self.base_path = cacher.setup.prepare_cache(self.task_id)

        # Write user libs to input directory
        self.write_user_libs()

    def cleanup(self):
        ''' Removes all files in cache for a passed task_id '''
        logger.debug("Cleanup cache for task '%s'" % self.task_id)

        try:
            shutil.rmtree(self.base_path)
        except:
            logger.error(traceback.format_exc())

    def write_file_to_input(self, filename, content):
        file = os.path.join(self.input_path, filename)

        with open(file, "w") as output_file:
            output_file.write(content)

    def write_script(self, script):
        self.write_file_to_input("script", script)

    def write_user_libs(self):
        module_dir = os.path.dirname(__file__)
        src_lib_dir = os.path.join(module_dir, "..", "user_libs")
        dst_lib_dir = os.path.join(self.input_path, _user_libs_dirname)

        shutil.copytree(src_lib_dir, dst_lib_dir)

    def upload_output_files(self, data_provider, destination, **kwargs):
        upload_futures = []
        for root, _, files in os.walk(self.output_path):
            for file in files:
                upload_futures.append(self.add_upload_task(data_provider, os.path.join(root, file), destination, file, **kwargs))

        return upload_futures

    def add_download_task(self, data_provider, source, filename, **kwargs):
        dp = data_provider(**kwargs)

        dest_file = os.path.join(self.input_path, filename)
        cache_path = cacher.setup.get_cache_path()

        # Try to get the file hash from the dataprovider. In case a hash is not available, dp will return None
        file_hash = dp.get_hash(source)

        # Check local cache
        if file_hash is not None:
            cached_file = os.path.join(cache_path, filename + "-" + file_hash)

            if os.path.isfile(cached_file):
                # Copy file from local cache to input path from task
                logger.debug("Found file with hash '%s' in local cache - starting copy to '%s'" % (file_hash, dest_file))
                return cacher.setup.add_task(cacher.tasks.CacherTask(shutil.copyfile, cached_file, dest_file))


        # Make sure download is complete and file is copied to local cache before continuing
        def download_and_cache(dp=dp, source=source, dest_file=dest_file, filename=filename, file_hash=file_hash, cache_path=cache_path):
            dp.download_file(source, dest_file)

            if file_hash is not None:
                # File to copy to local cache (source) is the destination of the download-task
                logger.debug("Starting copy from '%s' to local cache with hash '%s'" % (source, file_hash))
                shutil.copyfile(dest_file, os.path.join(cache_path, filename + "-" + file_hash))
                logger.debug("Finished copy from '%s' to local cache with hash '%s'" % (source, file_hash))

        # dp does not support hashing or file is not in local cache -> download it
        fut = cacher.setup.add_task(cacher.tasks.CacherTask(download_and_cache))

        return fut

    def add_upload_task(self, data_provider, filename, destination_path, destination_filename, **kwargs):
        dp = data_provider(**kwargs)

        fut = cacher.setup.add_task(cacher.tasks.CacherTask(dp.upload_file, filename, destination_path, destination_filename))
        return fut
