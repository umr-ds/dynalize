'''
@author: PUM
'''
from cloud_providers.ec2provider import Ec2CloudProvider

import database
import log
from database.model.instance import Instance
from threading import Thread
from database.model.clouddef import CloudDef
import app_exceptions
from boto.exception import EC2ResponseError
from app_exceptions import InvalidSnapshotException, InvalidInstanceException
import decorators
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import joinedload
import json

logger = log.setup_logger(__name__)

class CloudManager():
    ''' '''
    def __init__(self, clouddef_id):
        '''
        :param clouddef_id: ID of the corresponding cloud database entry
        '''
        self.clouddef_id = clouddef_id


    @decorators.lazyproperty
    def cloud_data(self):
        with database.get_session() as session:
            try:
                # Make sure we actually query all data (including all relations) as the session will be closed afterwards and a lazy evaluation is only possible after reattaching to a session
                return session.query(CloudDef).filter(CloudDef.clouddef_id == self.clouddef_id).options(joinedload("*")).one()
            except (NoResultFound, MultipleResultsFound):
                raise app_exceptions.UnknownCloudException()

    @decorators.lazyproperty
    def cloud_provider(self):
        if self.cloud_data.cloudprovider_id == 1:
            # EC2
            return Ec2CloudProvider(self.cloud_data.clouddefec2_relation.access_key, self.cloud_data.clouddefec2_relation.secret_key)
        else:
            raise app_exceptions.UnknownCloudException()

    @decorators.allow_async_execution
    def check_instance_database_cache(self):
        ''' Checks all instances in the database and checks if they really exist in the cloud. '''
        with database.get_session() as session:
            logger.debug("Checking instance database for invalid entries.")
            database_instances = session.query(Instance).filter(Instance.clouddef_id == self.clouddef_id).all()

            #print(self.cloud_provider)
            for database_instance in database_instances:
                instance_status = self.cloud_provider.instance_status(database_instance.provider_id)

                if instance_status is None or instance_status == 'terminated':
                    # Instance exists in DB but not in cloud
                    logger.warn("Removing invalid instance entry '%s' from database." % database_instance.provider_id)
                    session.delete(database_instance)
                else:
                    logger.debug("Instance '%s' status is '%s'" % (database_instance.provider_id, database_instance.status))
                    database_instance.status = instance_status.title()

            session.commit()

    @decorators.allow_async_execution
    def stop_instance(self, instance_id):
        try:
            with database.get_session() as session:
                database_instance = session.query(Instance).filter(Instance.instance_id == instance_id).one()
                self.cloud_provider.stop_instance(database_instance.provider_id)

                database_instance.status = "Stopping"
                session.commit()
        except (NoResultFound, MultipleResultsFound):
            raise InvalidInstanceException("Can't stop instance, invalid instance ID")

    @decorators.allow_async_execution
    def start_instance(self, instance_id):
        try:
            with database.get_session() as session:
                database_instance = session.query(Instance).filter(Instance.instance_id == instance_id).one()
                self.cloud_provider.start_instance(database_instance.provider_id)

                database_instance.status = "Starting"
                session.commit()
        except (NoResultFound, MultipleResultsFound):
            raise InvalidInstanceException("Can't start instance, invalid instance ID")

    @decorators.allow_async_execution
    def terminate_instance(self, instance_id):
        try:
            with database.get_session() as session:
                database_instance = session.query(Instance).filter(Instance.instance_id == instance_id).one()
                self.cloud_provider.terminate_instance(database_instance.provider_id)

                database_instance.status = "Terminating"
                session.commit()
        except (NoResultFound, MultipleResultsFound):
            raise InvalidInstanceException("Can't terminate instance, invalid instance ID")

    @decorators.allow_async_execution
    def launch_instances(self, number_of_instances=1, instance_type='t2.medium'):
        if self.cloud_data.cloudprovider_id == 1:
            # EC 2

            with database.get_session() as session:
                try:
                    startup_queue = " -q cloud-" + self.cloud_data.clouddef_id

                    instances = self.cloud_provider.launch_instance(
                                                                    self.cloud_data.snapshot_image_id,
                                                                    self.cloud_data.clouddefec2_relation.keypair,
                                                                    [self.cloud_data.clouddefec2_relation.security_group],
                                                                    self.cloud_data.clouddefec2_relation.subnet,
                                                                    instance_type=instance_type,
                                                                    min_count = number_of_instances,
                                                                    max_count = number_of_instances,
                                                                    user_data = json.dumps({'dynalize_parameter' : self.cloud_data.client_startup_parameters + startup_queue})
                                                                    )
                    for inst in instances:
                        new_instance = Instance(
                                clouddef_id = self.cloud_data.clouddef_id,
                                comment = "Worker Instance '%s'" % instance_type,
                                provider_id = inst.id,
                                provider_name = inst.tags.get('Name', ""),
                                status = "Starting"
                                )

                        session.add(new_instance)

                    session.commit()
                except EC2ResponseError as exc:
                    if "InvalidAMIID.Malformed" in str(exc) or "InvalidAMIID.NotFound" in str(exc):
                        logger.error("Invalid AMI stored in database. Deleting the invalid entry.")
                        raise InvalidSnapshotException("Invalid AMI stored in database. Deleting the invalid entry.")

                    # Otherwise raise the original error
                    raise

    @decorators.allow_async_execution
    def instance_to_snapshot(self, instance_id, snapshot_name):
        try:
            self.check_instance_database_cache()

            with database.get_session() as session:
                database_instance = session.query(Instance).filter(Instance.instance_id == instance_id).one()

                database_instance.status = "Creating Snapshot"
                session.commit()

                snapshot_id, image_id = self.cloud_provider.instance_to_snapshot(database_instance.provider_id, snapshot_name)

                if snapshot_id is not None and image_id is not None:
                    inst = session.query(CloudDef).filter(CloudDef.clouddef_id == self.cloud_data.clouddef_id).one()
                    inst.snapshot_id = snapshot_id
                    inst.snapshot_image_id = image_id
                    session.commit()

        except (NoResultFound, MultipleResultsFound):
            raise InvalidInstanceException("Can't terminate instance, invalid instance ID")

    @decorators.allow_async_execution
    def deploy_to_snapshot(self, snapshot_name, shutdown_and_take_snapshot=True, instance_type='t2.medium'):
        if self.cloud_data.test_layer_relation is None:
            raise ValueError("Missing test layer")

        if self.cloud_data.virtual_device_layer_relation is None:
            raise ValueError("Missing virtual device layer")

        if self.cloud_data.cloudprovider_id == 1:
            # EC2
            if self.cloud_data.snapshot_image_id is not None and len(self.cloud_data.snapshot_image_id) > 0:
                logger.warn("Found old image '%s' in database -> removing it" % self.cloud_data.snapshot_image_id)

                logger.debug("Try to find the snapshot-id of the image '%s' before removing." % self.cloud_data.snapshot_image_id)
                snapshot_id = self.cloud_provider.get_snapshot_from_image(self.cloud_data.snapshot_image_id)

                self.cloud_provider.remove_image(self.cloud_data.snapshot_image_id)

                # This is needed in rare cases when the snapshot_id could not be determined at the snapshot creation
                # Alternative: Let boto do the job for us und use delete_snapshot=True on deregister_image
                if snapshot_id is not None:
                    logger.debug("Found snapshot-id '%s' -> remove it." % snapshot_id)
                    self.cloud_provider.remove_snapshot(snapshot_id)


            if self.cloud_data.snapshot_id is not None and len(self.cloud_data.snapshot_id) > 0:
                logger.warn("Found old snapshot '%s' in database -> removing it" % self.cloud_data.snapshot_id)
                self.cloud_provider.remove_snapshot(self.cloud_data.snapshot_id)

            startup_queue = " -q cloud-" + self.cloud_data.clouddef_id

            instances = self.cloud_provider.initial_deployment(
                                                               self.cloud_data.clouddefec2_relation.base_ami,
                                                               self.cloud_data.clouddefec2_relation.keypair,
                                                               [self.cloud_data.clouddefec2_relation.security_group],
                                                               self.cloud_data.clouddefec2_relation.subnet,
                                                               instance_type=instance_type,
                                                               deploy_shutdown=shutdown_and_take_snapshot,
                                                               deploy_parameter=self.cloud_data.client_startup_parameters + startup_queue,
                                                               virtual_device_layer=self.cloud_data.virtual_device_layer_relation,
                                                               test_layer=self.cloud_data.test_layer_relation
                                                               )

            inst = instances[0]

            with database.get_session() as session:
                new_instance = Instance(
                                        clouddef_id = self.cloud_data.clouddef_id,
                                        comment = "Deployment instance",
                                        provider_id = inst.id,
                                        provider_name = inst.tags.get('Name', "")
                                        )

                session.add(new_instance)
                session.commit()

                if shutdown_and_take_snapshot:
                    def deployment_finished(snapshot_id, image_id, clouddef_id=self.cloud_data.clouddef_id, instance_id=new_instance.instance_id):
                        with database.get_session() as session:
                            inst = session.query(Instance).filter(Instance.instance_id == instance_id).one()
                            session.delete(inst)
                            session.commit()

                            inst = session.query(CloudDef).filter(CloudDef.clouddef_id == clouddef_id).one()
                            inst.snapshot_id = snapshot_id
                            inst.snapshot_image_id = image_id
                            session.commit()

                    t = Thread(target=self.cloud_provider.take_snapshot_after_shutdown, args=(inst, snapshot_name, deployment_finished, ))
                    t.start()
