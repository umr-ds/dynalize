'''
@author: PUM
'''
import dockerhelper
import log
import signal
import os
import atexit
import hashlib
import traceback

from docker.client import Client
from io import BytesIO
from docker.errors import APIError
from requests.exceptions import HTTPError

logger = log.setup_logger(__name__)

class DockerContainer():
    def __init__(self, container, manager):
        self.container = container
        self.manager = manager

    def get_id(self):
        return self.container.get('Id')

    def output(self, **kwargs):
        conn = self.manager._get_connection()

        return conn.logs(self.get_id(), **kwargs)

    def is_running(self):
        conn = self.manager._get_connection()

        return conn.inspect_container(self.get_id())['State']['Running']

    def remove(self):
        conn = self.manager._get_connection()

        try:
            self.stop()
        except:
            pass

        logger.debug("Removing container '%s'" % self.get_id())

        try:
            conn.remove_container(self.get_id())

            # Try to remove this container from the list of running containers
            self.manager.containers.remove(self)
        except:
            logger.error("Failed to remove container '%s'" % self.get_id())

    def wait_until_stopped(self, timeout=None):
        conn = self.manager._get_connection()

        if timeout == 0:
            timeout = None

        try:
            # In case of using http to connect to docker an exception is raised when a timeout occurs
            return conn.wait(self.get_id(), timeout)
        except:
            pass

    def stop(self):
        conn = self.manager._get_connection()

        logger.debug("Stopping container '%s'" % self.get_id())

        conn.stop(self.get_id())

class DockerVolume():
    def __init__(self, real_path, container_path, readonly=False):
        self.real_path = os.path.abspath(real_path)
        self.container_path = container_path
        self.readonly = readonly

    @staticmethod
    def get_create_container_list(volumelist):
        try:
            return [x.container_path for x in volumelist]
        except TypeError:
            return None

    @staticmethod
    def get_start_list(volumelist):
        temp_list = {}

        try:
            for vol in volumelist:
                temp_list[vol.real_path] = {}
                temp_list[vol.real_path]['bind'] = vol.container_path
                temp_list[vol.real_path]['ro'] = vol.readonly
        except TypeError:
            return None

        return temp_list

class DockerManager():
    def __init__(self, url='unix://var/run/docker.sock'):
        self.url = url

        self.conn = None
        self.containers = []
        self.known_layer = {}

        # Make sure we clean up all containers at exit
        atexit.register(self.remove_all_containers)

    def _get_connection(self):
        if self.conn is None:
            self.conn = Client(base_url=self.url)

        return self.conn

    def is_working(self):
        conn = self._get_connection()
        return conn.ping()

    def run(self, image_id, env_dict=None, volumelist=None):
        conn = self._get_connection()

        logger.debug("Starting container with image '%s'" % image_id)

        container = conn.create_container(image=image_id,
                                          environment=env_dict,
                                          volumes=DockerVolume.get_create_container_list(volumelist)
                                          )

        conn.start(container=container.get('Id'),
                   binds=DockerVolume.get_start_list(volumelist)
                   )

        logger.debug("Container with id '%s' started" % container.get('Id'))

        docker_container = DockerContainer(container, self)
        self.containers.append(docker_container)

        return docker_container

    def is_image_available(self, name):
        conn = self._get_connection()

        return (len(conn.images(name, quiet=True)) > 0)

    def remove_all_containers(self):
        logger.debug("Removing all containers started by this manager...")

        for container in self.containers:
            try:
                container.stop()
            except:
                pass

            try:
                container.remove()
            except:
                pass

    def build_with_cache(self, layer_data, layer_tag=None):
        ''' Checks the internal layer cache and builds the layer if needed. Returns the layer id in both cases '''
        hash_content = (layer_data).encode('utf-8')
        md5_layer = hashlib.md5(hash_content).hexdigest().lower()
        try:
            if not md5_layer in self.known_layer:
                image_id, build_log = self.build(layer_data, layer_tag)
                self.known_layer[md5_layer] = image_id
            else:
                image_id = self.known_layer[md5_layer]
                build_log = ["Using internal cache\n"]

            return image_id, build_log
        except:
            traceback.print_exc()
            raise

    def build(self, layer_data, layer_tag=None):
        ''' Builds the layer and returns the id and the build log of the created image, None if no id was found '''
        conn = self._get_connection()

        content = BytesIO(layer_data.encode('utf-8'))
        result = conn.build(
                            fileobj=content, rm=True, tag=layer_tag
                            )

        return dockerhelper.get_build_id(result)



    def build_from_json(self, json_data, build_each_layer=False):
        # When using files:
        #f = open("Dockerfiles/test", "rb")

        # When using strings:
        #dockerfile = ''' ... '''
        #f = BytesIO(dockerfile.encode('utf-8'))

        data = json_data['data']

        if build_each_layer:
            last_image = None
            last_id = None

            for layer in data:
                # Make sure the layers are built on top of each other
                if last_image is not None:
                    layer['content'] = "FROM " + last_image + "\n" + layer['content']

                last_id = self.build(layer['content'], layer['tag'])

                last_image = layer['tag']

            return last_id
        else:
            content = ""
            last_tag = None

            for layer in data:
                content += layer['content'] + "\n"
                last_tag = layer['tag']

            # When only building one full layer, we tag it with the tag of the last layer
            # as this tag most likely will be used for reference in a run layer
            return self.build(content, last_tag)
