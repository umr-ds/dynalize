'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext import restful
from flask.ext.restful import fields
from common_api.json import json_status
from common_api.customfields import BpUrl
from database.model.instance import Instance
from cloud_providers.cloudmanager import CloudManager

# Prefix for all API calls served by this script
api_prefix = "/instance"

# Marhsalling information for datastructures used by this script
def _get_instance_fields():
    return {
            'instance_id' : fields.Integer,
            'clouddef_id' : fields.Integer,
            'hostname' : fields.String,
            'comment' : fields.String,
            'provider_id' : fields.String,
            'provider_name' : fields.String,
            'status' : fields.String,
            'uri' : BpUrl(api_restful, InstanceApi, absolute=True)
            }

def _get_instance(instance_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(Instance).filter(Instance.instance_id == instance_id), session)

def _get_all_instances():
    with database.get_session() as session:
        inst = session.query(Instance).order_by(Instance.instance_id).all()
        return inst


# Endpoint definitions
class InstanceList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_instances, None, _get_instance_fields)

    def post(self):
        return json_status(False, 405, "Instance are readonly through the api.")


class InstanceApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_instance, None, _get_instance_fields, "instance_id")

    def delete(self, **kwargs):
        return json_status(False, 405, "Instance are readonly through the api.")

    def put(self, **kwargs):
        return json_status(False, 405, "Instance are readonly through the api.")

class InstanceApiDetails(restful.Resource):
    def post(self, instance_id, action):
        action = action.lower()

        inst = _get_instance(instance_id)[0]
        cm = CloudManager(inst.clouddef_id)

        if action == "stop":
            cm.stop_instance(instance_id)
        elif action == "start":
            cm.start_instance(instance_id)
        elif action == "terminate":
            cm.terminate_instance(instance_id)
        elif action == "createsnapshot":
            cm.instance_to_snapshot(instance_id, "Manual snapshot")


# Registering all ressources/endpoints served by this script
api_restful.add_resource(InstanceList, api_prefix)
api_restful.add_resource(InstanceApi, api_prefix + "/<int:instance_id>")
api_restful.add_resource(InstanceApiDetails, api_prefix + "/<int:instance_id>/<string:action>")
