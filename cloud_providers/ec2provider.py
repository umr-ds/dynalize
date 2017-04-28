'''
@author: PUM
'''
from cloud_providers.basecloudprovider import BaseCloudProvider
import boto.ec2
import time
import deployment
import datetime
import log
import re
from boto.exception import EC2ResponseError

logger = log.setup_logger(__name__)

re_url_app = re.compile("{{deploy_url_app}}", re.IGNORECASE)
re_parameter = re.compile("{{deploy_parameter}}", re.IGNORECASE)
re_shutdown = re.compile("{{deploy_shutdown}}", re.IGNORECASE)

class Ec2CloudProvider(BaseCloudProvider):
    def __init__(self, access_key=None, secret_key=None, region='eu-west-1'):
        ''' If no aws-credentials specified, boto will use aws-cred. defined in environment vars or config files. See http://boto.readthedocs.org/en/latest/boto_config_tut.html '''
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

        # Boto treats an empty string as an passed credential. To workaround a potential wrong database entry, make sure we use None in this case
        if self.access_key == '': self.access_key = None
        if self.secret_key == '': self.secret_key = None

        self.conn = None


    def _get_connection(self):
        if self.conn is None:
            self.conn = boto.ec2.connect_to_region(self.region,
                                                   aws_access_key_id = self.access_key,
                                                   aws_secret_access_key = self.secret_key
                                                   )

        return self.conn

    def take_snapshot_after_shutdown(self, inst, snapshot_name, func_finished=None):
        while inst.state != 'running':
            logger.debug("Waiting for instance '%s' to enter running state" % inst.id)
            time.sleep(10)
            inst.update()

        while inst.state != 'stopped':
            logger.debug("Waiting for instance '%s' to enter stopped state" % inst.id)
            time.sleep(10)
            inst.update()

        logger.debug("Instance '%s' entered stopped stated -> taking snapshot '%s'" % (inst.id, snapshot_name))

        snapshot_id, image_id = self.instance_to_snapshot(inst.id, snapshot_name)

        logger.debug("Created snapshot '%s' of instance '%s' -> terminating the instance now" % (snapshot_name, inst.id))
        inst.terminate()

        if func_finished is not None:
            func_finished(snapshot_id, image_id)


    def _get_init_script(self, deploy_url_app, deploy_parameter, deploy_shutdown=True):
        init_script = open("cloud_providers/scripts/ec2init.sh", "r").read()

        # Replace deployment parameters, use regex to have a case insensitive replace
        init_script = re_url_app.sub(deploy_url_app, init_script)
        init_script = re_parameter.sub(deploy_parameter, init_script)

        if deploy_shutdown:
            init_script = re_shutdown.sub(str(1), init_script)
        else:
            init_script = re_shutdown.sub(str(0), init_script)

        return init_script

    def instance_to_snapshot(self, instance_id, snapshot_name, description=""):
        ''' Returns (snapshot_id, image_id) '''
        def take_snapshot(instance_id, snapshot_name, description=""):
            conn = self._get_connection()

            image_id = conn.create_image(instance_id, snapshot_name, description)
            snapshot_id = None

            # Try to get the snapshot id from the image. This takes a while, so try multiple times
            for _ in range(5):
                if snapshot_id is None:
                    snapshot_id = self.get_snapshot_from_image(image_id)

                    time.sleep(5)
                else:
                    break

            return snapshot_id, image_id

        # Make sure we actually create a snapshot and don't get a duplicate snapshot_name exception
        try:
            snapshot_id, image_id = take_snapshot(instance_id, snapshot_name, description)
        except EC2ResponseError as exc:
            if "InvalidAMIName.Duplicate" in str(exc):
                # In case the snapshot_name is already in use, we automatically append the current datetime to the snapshot_name
                logger.error("Snapshot creation failed, trying to append current datetime. Exception: '%s'" % str(exc))
                snapshot_id, image_id = self.instance_to_snapshot(instance_id, snapshot_name + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"), description)
            else:
                logger.error("Snapshot creation failed with '%s'" % str(exc))
                snapshot_id, image_id = None, None

        return snapshot_id, image_id

    def get_snapshot_from_image(self, image_id):
        conn = self._get_connection()

        try:
            image = conn.get_image(image_id)

            for _, block_obj in image.block_device_mapping.items():
                if block_obj.snapshot_id is not None and len(block_obj.snapshot_id) > 0:
                    return block_obj.snapshot_id
        except:
            pass

        return None

    def initial_deployment(self, ami, key_name, security_group_ids, subnet_id, instance_type, deploy_shutdown, virtual_device_layer, test_layer, deploy_parameter="", **kwargs):
        logger.debug("Starting deployment")

        # Create archive with deploy.json file
        deployment.create_deploy_json_file(virtual_device_layer, test_layer)
        url_app = deployment.selfdeploy_to_s3()
        deployment.remove_deploy_json_file()

        init_script = self._get_init_script(url_app, deploy_parameter, deploy_shutdown)

        logger.debug("Starting deployment instance")
        instances = self.launch_instance(ami=ami, key_name=key_name, security_group_ids=security_group_ids, subnet_id=subnet_id,instance_type=instance_type, user_data=init_script, **kwargs)

        return instances


    def launch_instance(self, ami, key_name, security_group_ids, subnet_id, instance_type, user_data="", **kwargs):
        conn = self._get_connection()

        reservation = conn.run_instances(image_id=ami, key_name=key_name, security_group_ids=security_group_ids, subnet_id=subnet_id, instance_type=instance_type, user_data=user_data, **kwargs)
        return reservation.instances


    def start_instance(self, instance_id):
        conn = self._get_connection()

        logger.debug("Starting instance '%s'" % instance_id)
        inst = conn.get_only_instances(instance_ids=[instance_id])
        inst[0].start()

        return True

    def stop_instance(self, instance_id):
        conn = self._get_connection()

        logger.debug("Stopping instance '%s'" % instance_id)
        conn.stop_instances(instance_ids=[instance_id])

        return True

    def terminate_instance(self, instance_id):
        conn = self._get_connection()

        logger.debug("Terminating instance '%s'" % instance_id)
        conn.terminate_instances(instance_ids=[instance_id])

        return True

    def instance_status(self, instance_id):
        conn = self._get_connection()

        logger.debug("Getting status of instance '%s'" % instance_id)

        instances = conn.get_only_instances(instance_ids=[instance_id])

        try:
            return instances[0].state
        except:
            return None

    def remove_snapshot(self, snapshot_id):
        conn = self._get_connection()

        logger.debug("Removing snapshot '%s'" % snapshot_id)

        try:
            snapshots = conn.get_all_snapshots(snapshot_ids=[snapshot_id])
            snapshot = snapshots[0]

            snapshot.delete()
        except (IndexError, EC2ResponseError):
            return False

        return True

    def remove_image(self, image_id):
        conn = self._get_connection()

        logger.debug("Removing image '%s'" % image_id)

        try:
            images = conn.get_all_images(image_ids=[image_id])
            image = images[0]

            image.deregister()
        except (IndexError, EC2ResponseError):
            return False

        return True
