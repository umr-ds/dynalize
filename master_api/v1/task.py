'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext import restful
from flask.ext.restful import fields
from common_api.json import json_status
from common_api.customfields import BpUrl
from database.model.task import Task
from masterscheduler import MasterScheduler

# Prefix for all API calls served by this script
api_prefix = "/task"

# Marhsalling information for datastructures used by this script
def _get_task_fields():
    return {
            'task_id' : fields.Integer,
            'job_id' : fields.Integer,
            'filename' : fields.String,
            'backend_id' : fields.String,
            'worker_hostname' : fields.String,
            'created_on' : fields.DateTime,
            'completed' : fields.Boolean,
            'output' : fields.String,
            'build_logs' : fields.String,
            'exception' : fields.String,
            'traceback' : fields.String,
            'exit_code' : fields.String,
            'duration' : fields.Float,
            'uri' : BpUrl(api_restful, TaskApi, absolute=True)
            }

def _get_task(task_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(Task).filter(Task.task_id == task_id), session)

def _get_all_tasks():
    with database.get_session() as session:
        inst = session.query(Task).order_by(Task.task_id).all()
        return inst

# Endpoint definitions
class TaskList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_tasks, None, _get_task_fields)

    def post(self):
        return json_status(False, 405, "Tasks are readonly through the api.")


class TaskApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_task, None, _get_task_fields, "task_id")

    def delete(self, task_id):
        ms = MasterScheduler()
        ms.remove_task(task_id)

    def put(self, **kwargs):
        return json_status(False, 405, "Tasks are readonly through the api.")

class TaskApiDetails(restful.Resource):
    def post(self, task_id, action):
        action = action.lower()

        if action == "test":
            pass

# Registering all ressources/endpoints served by this script
api_restful.add_resource(TaskList, api_prefix)
api_restful.add_resource(TaskApi, api_prefix + "/<int:task_id>")
api_restful.add_resource(TaskApiDetails, api_prefix + "/<int:task_id>/<string:action>")
