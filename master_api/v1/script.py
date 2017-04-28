'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext.restful import fields
from database.model.script import Script
from common_api.json import json_status
from common_api.customfields import BpUrl
from common_api import customfields

# Prefix for all API calls served by this script
api_prefix = "/script"

# Marhsalling information for datastructures used by this script
def _get_script_fields():
    details_fields = _get_script_details_fields()
    del details_fields['content']
    return details_fields

def _get_script_details_fields():
    return {
            'script_id' : fields.Integer,
            'name' : fields.String,
            'content' : fields.String,
            'modified_on' : customfields.CustomDateTime,
            'uri' : BpUrl(api_restful, ScriptApi, absolute=True)
            }

def _get_script(script_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(Script).filter(Script.script_id == script_id), session)

def _get_all_scripts():
    with database.get_session() as session:
        inst = session.query(Script).order_by(Script.name).all()

        return inst

def _merge_script(json_data, script_id=None):
    if json_data is None or not 'name' in json_data or not 'content' in json_data:
        return json_status(False, 400, "Missing required parameters")

    with database.get_session() as session:
        new_script = Script(
                            script_id = script_id,
                            name=json_data['name'],
                            content=json_data['content']
                            )

        new_script = session.merge(new_script)
        session.commit()

        return json_status(True, url=api_restful.url_for(ScriptApi, script_id=new_script.script_id))

# Endpoint definitions
class ScriptList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_scripts, _merge_script, _get_script_fields)


class ScriptApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_script, _merge_script, _get_script_details_fields, "script_id")


# Registering all ressources/endpoints served by this script
api_restful.add_resource(ScriptList, api_prefix)
api_restful.add_resource(ScriptApi, api_prefix + "/<int:script_id>")
