'''
@author: PUM
'''
import database
from flask.ext import restful
from flask.ext.restful import marshal, fields
from database.model.dataprovider import DataProvider
from common_api.json import json_response
from common_api.customfields import BpUrl
from . import api_restful

# Prefix for all API calls served by this script
api_prefix = "/dataprovider"

# Marhsalling information for datastructures used by this script
def _get_dataprovidertype_fields():
    return {
            'dataprovider_id' : fields.Integer,
            'name' : fields.String,
            'uri' : BpUrl(api_restful, DatProviderTypeList, absolute=True)
            }

class DatProviderTypeList(restful.Resource):
    def get(self):
        with database.get_session() as session:
            inst = session.query(DataProvider).order_by(DataProvider.dataprovider_id).all()
            return json_response(marshal(inst, _get_dataprovidertype_fields()))


# Registering all ressources/endpoints served by this script
api_restful.add_resource(DatProviderTypeList, api_prefix)
