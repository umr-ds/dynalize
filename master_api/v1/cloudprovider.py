'''
@author: PUM
'''
import database
from flask.ext import restful
from flask.ext.restful import marshal, fields
from database.model.cloudprovider import CloudProvider
from common_api.json import json_response
from common_api.customfields import BpUrl
from . import api_restful

# Prefix for all API calls served by this script
api_prefix = "/cloudprovider"

# Marhsalling information for datastructures used by this script
def _get_cloudtype_fields():
    return {
            'cloudprovider_id' : fields.Integer,
            'name' : fields.String,
            'uri' : BpUrl(api_restful, CloudTypeList, absolute=True)
            }

class CloudTypeList(restful.Resource):
    def get(self):
        with database.get_session() as session:
            inst = session.query(CloudProvider).order_by(CloudProvider.name).all()
            return json_response(marshal(inst, _get_cloudtype_fields()))


# Registering all ressources/endpoints served by this script
api_restful.add_resource(CloudTypeList, api_prefix)
