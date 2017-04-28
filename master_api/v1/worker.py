'''
@author: PUM
'''

from . import api_restful
from flask.ext.restful import fields
from common_api.json import  json_response
import celerycontrol
from flask_restful import marshal
from flask.ext import restful

# Prefix for all API calls served by this script
api_prefix = "/worker"

# Marhsalling information for datastructures used by this script
def _get_worker_fields():
    return {
            'hostname' : fields.String
            }


# Endpoint definitions
class WorkerList(restful.Resource):
    def get(self):
        worker = celerycontrol.get_running_worker()
        worker_list = []

        for w in worker:
            worker_list.append({'hostname' : str(w)})

        return json_response(marshal(worker_list, _get_worker_fields()))


# Registering all ressources/endpoints served by this script
api_restful.add_resource(WorkerList, api_prefix)
