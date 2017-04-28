'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext import restful
from flask.ext.restful import fields
from common_api.json import json_status
from common_api.customfields import BpUrl
from database.model.job import Job
from masterscheduler import MasterScheduler

# Prefix for all API calls served by this script
api_prefix = "/job"

# Marhsalling information for datastructures used by this script
def _get_instance_fields():
    return {
            'job_id' : fields.Integer,
            'clouddef_id' : fields.Integer,
            'run_layer_id' : fields.Integer(default=None),
            'script_id' : fields.Integer(default=None),
            'source_datadef_id' : fields.Integer(default=None),
            'destination_datadef_id' : fields.Integer(default=None),
            'name' : fields.String,
            'task_timeout' : fields.Integer,
            'uri' : BpUrl(api_restful, JobApi, absolute=True)
            }

def _get_instance(job_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(Job).filter(Job.job_id == job_id), session)

def _get_all_instances():
    with database.get_session() as session:
        inst = session.query(Job).order_by(Job.name).all()
        return inst

def _merge_job(json_data, job_id=None):
    if json_data is None or not 'name' in json_data or not 'clouddef_id' in json_data:
        return json_status(False, 400, "Missing required parameters")

    with database.get_session() as session:
        new_job = Job(
                      job_id        = job_id,
                      clouddef_id      = json_data.get('clouddef_id'),
                      run_layer_id  = json_data.get('run_layer_id', None),
                      script_id     = json_data.get('script_id', None),
                      source_datadef_id        = json_data.get('source_datadef_id', None),
                      destination_datadef_id   = json_data.get('destination_datadef_id', None),
                      name          = json_data.get('name'),
                      task_timeout  = json_data.get('task_timeout', 0)
                      )

        if new_job.run_layer_id == "0": new_job.run_layer_id = None
        if new_job.script_id == "0": new_job.script_id = None

        # Merge will automatically add a new instance if the primary key does not already exist
        new_job = session.merge(new_job)
        session.commit()

        return json_status(True, url=api_restful.url_for(JobApi, job_id=new_job.job_id))


# Endpoint definitions
class JobList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_instances, _merge_job, _get_instance_fields)


class JobApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_instance, _merge_job, _get_instance_fields, "job_id")

class JobApiDetails(restful.Resource):
    def post(self, job_id, action):
        action = action.lower()

        if action == "execute":
            ms = MasterScheduler()
            ms.add_job(job_id)

# Registering all ressources/endpoints served by this script
api_restful.add_resource(JobList, api_prefix)
api_restful.add_resource(JobApi, api_prefix + "/<int:job_id>")
api_restful.add_resource(JobApiDetails, api_prefix + "/<int:job_id>/<string:action>")
