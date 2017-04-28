'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext import restful
from flask.ext.restful import marshal, fields
from database.model.clouddef import CloudDef, CloudDefEc2
from common_api.json import json_response, json_status, json_success
from common_api.customfields import BpUrl
from cloud_providers.cloudmanager import CloudManager
from flask.globals import request
from sqlalchemy.orm.exc import NoResultFound

# Prefix for all API calls served by this script
api_prefix = "/clouddef"

# Marhsalling information for datastructures used by this script
def _get_cloud_fields():
    return {
            'clouddef_id' : fields.Integer,
            'name' : fields.String,
            'cloudprovider_id' : fields.Integer(default=None),              # Make sure we actually get "null" and not "0"
            'virtual_device_layer_id' : fields.Integer(default=None),   # Make sure we actually get "null" and not "0"
            'test_layer_id' : fields.Integer(default=None),             # Make sure we actually get "null" and not "0"
            'snapshot_id' : fields.String,
            'snapshot_image_id' : fields.String,
            'client_startup_parameters' : fields.String,
            'uri' : BpUrl(api_restful, CloudApi, absolute=True)
            }

def _get_ec2_fields():
    return {
            'clouddefec2_id' : fields.Integer,
            'base_ami' : fields.String,
            'keypair' : fields.String,
            'security_group' : fields.String,
            'subnet' : fields.String,
            'access_key' : fields.String,
            'secret_key' : fields.String
            }

def _merge_cloud(json_data, clouddef_id=None):
    if json_data is None or not 'name' in json_data or not 'cloudprovider_id' in json_data:
        return json_status(False, 400, "Missing required parameters")

    with database.get_session() as session:
        new_cloud = CloudDef(
                          name = json_data.get('name'),
                          cloudprovider_id = json_data.get('cloudprovider_id'),
                          virtual_device_layer_id = json_data.get('virtual_device_layer_id', None),
                          test_layer_id = json_data.get('test_layer_id', None),
                          client_startup_parameters = json_data.get('client_startup_parameters', None)
                          )

        if str(new_cloud.virtual_device_layer_id) == "0": new_cloud.virtual_device_layer_id = None
        if str(new_cloud.test_layer_id) == "0": new_cloud.test_layer_id = None

        if clouddef_id is not None:
            new_cloud.clouddef_id = clouddef_id

        new_cloud = session.merge(new_cloud)
        session.commit()

        _merge_ec2(json_data, new_cloud)

        return json_status(True, url=api_restful.url_for(CloudApi, clouddef_id=new_cloud.clouddef_id))

def _merge_ec2(json_data, new_cloud):
    if not new_cloud.cloudprovider_id == 1:
        # Looks like no EC2 cloud was created
        return

    with database.get_session() as session:
        new_ec2 = CloudDefEc2(
                           clouddef_id = new_cloud.clouddef_id,
                           base_ami = json_data.get('base_ami'),
                           keypair = json_data.get('keypair', None),
                           security_group = json_data.get('security_group', None),
                           subnet = json_data.get('subnet', None),
                           access_key = json_data.get('access_key', None),
                           secret_key = json_data.get('secret_key', None)
                          )

        try:
            ec2 = _get_cloudec2_query(new_cloud.clouddef_id)[0]
            new_ec2.clouddefec2_id = ec2.clouddefec2_id
        except NoResultFound:
            pass

        session.merge(new_ec2)
        session.commit()

def _get_cloud(clouddef_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(CloudDef).filter(CloudDef.clouddef_id == clouddef_id), session)

def _get_all_clouds():
    with database.get_session() as session:
        inst = session.query(CloudDef).order_by(CloudDef.name).all()
        return inst

def _get_cloudec2(clouddef_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(CloudDefEc2).filter(CloudDefEc2.clouddef_id == clouddef_id), session)

def _get_cloudec2_query(clouddef_id):
    with database.get_session() as session:
        return session.query(CloudDefEc2).filter(CloudDefEc2.clouddef_id == clouddef_id).one(), session

# Endpoint definitions
class CloudList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_clouds, _merge_cloud, _get_cloud_fields)


class CloudApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_cloud, _merge_cloud, _get_cloud_fields, "clouddef_id")

    def get(self, clouddef_id):
        inst = _get_cloud(clouddef_id)[0]

        cloud_dict = marshal(inst, _get_cloud_fields())

        if inst.cloudprovider_id == 1:
            try:
                # Try to get details off the details instance, otherwise only the main cloud info is returned
                details_inst = _get_cloudec2_query(inst.clouddef_id)[0]
                details_dict = marshal(details_inst, _get_ec2_fields())
                cloud_dict.update(details_dict)
            except (TypeError, NoResultFound):
                pass

        return json_response(cloud_dict)


class CloudApiDetails(restful.Resource):

    def post(self, clouddef_id, action):
        action = action.lower()
        json_data = request.get_json() or {}
        cm = CloudManager(clouddef_id)

        if action == "createsnapshot":
            if 'name' in json_data:
                snapshot_name = json_data['name']
            else:
                inst = _get_cloud(clouddef_id)[0]
                snapshot_name = inst.name

            cm.deploy_to_snapshot(snapshot_name, run_async=True)
        elif action == "startinstance":
            json_data = request.get_json()

            if json_data is None or not 'number_of_instances' in json_data:
                return json_status(False, 400, "Missing required parameters")

            number_of_instances = json_data['number_of_instances']
            instance_type = json_data.get('instance_type', None)

            cm.launch_instances(number_of_instances, instance_type, run_async=True)
        elif action == "refreshinstances":
            cm.check_instance_database_cache()

        elif action == "startdeploymentinstance":
            # Start an instance, start the deployment but do not take a snapshot automatically
            json_data = request.get_json() or {}

            instance_type = json_data.get('instance_type', 't2.medium')
            inst = _get_cloud(clouddef_id)[0]
            snapshot_name = inst.name
            cm.deploy_to_snapshot(snapshot_name, shutdown_and_take_snapshot=False, instance_type=instance_type, run_async=True)

        return json_success()


# Registering all ressources/endpoints served by this script
api_restful.add_resource(CloudList, api_prefix)
api_restful.add_resource(CloudApi, api_prefix + "/<int:clouddef_id>")
api_restful.add_resource(CloudApiDetails, api_prefix + "/<int:clouddef_id>/<string:action>")
