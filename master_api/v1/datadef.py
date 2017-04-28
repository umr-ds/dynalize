'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext import restful
from flask.ext.restful import marshal, fields
from common_api.json import json_response, json_status
from common_api.customfields import BpUrl
from sqlalchemy.orm.exc import NoResultFound
from database.model.datadef import DataDef, DataDefS3

# Prefix for all API calls served by this script
api_prefix = "/datadef"

# Marhsalling information for datastructures used by this script
def _get_dataprovider_fields():
    return {
            'datadef_id' : fields.Integer,
            'name' : fields.String,
            'dataprovider_id' : fields.Integer(default=None),
            'source' : fields.String,
            'source_path_filter' : fields.String,
            'source_filename_filter' : fields.String,
            'destination' : fields.String,
            'uri' : BpUrl(api_restful, DataProviderApi, absolute=True)
            }

def _get_s3_fields():
    return {
            'datadefs3_id' : fields.Integer,
            'bucket_name' : fields.String,
            'access_key' : fields.String,
            'secret_key' : fields.String
            }

def _merge_dataprovider(json_data, datadef_id=None):
    if json_data is None or not 'name' in json_data or not 'dataprovider_id' in json_data:
        return json_status(False, 400, "Missing required parameters")

    with database.get_session() as session:
        new_dataprovider = DataDef(
                                        name = json_data.get('name'),
                                        dataprovider_id = json_data.get('dataprovider_id'),
                                        source = json_data.get('source', None),
                                        source_path_filter = json_data.get('source_path_filter', None),
                                        source_filename_filter = json_data.get('source_filename_filter', None),
                                        destination = json_data.get('destination', None)
                                        )


        if datadef_id is not None:
            new_dataprovider.datadef_id = datadef_id

        new_dataprovider = session.merge(new_dataprovider)
        session.commit()

        _merge_s3(json_data, new_dataprovider)

        return json_status(True, url=api_restful.url_for(DataProviderApi, datadef_id=new_dataprovider.datadef_id))

def _merge_s3(json_data, new_dataprovider):
    if not new_dataprovider.dataprovider_id == 1:
        # Looks like no S3 Dataprovider was created
        return

    with database.get_session() as session:
        new_s3 = DataDefS3(
                               datadef_id = new_dataprovider.datadef_id,
                               bucket_name = json_data.get('bucket_name'),
                               access_key = json_data.get('access_key', None),
                               secret_key = json_data.get('secret_key', None)
                              )

        try:
            s3 = _get_dataproviders3_query(new_dataprovider.datadef_id)[0]
            new_s3.datadefs3_id = s3.datadefs3_id
        except NoResultFound:
            pass

        session.merge(new_s3)
        session.commit()

def _get_dataprovider(datadef_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(DataDef).filter(DataDef.datadef_id == datadef_id), session)

def _get_all_dataproviders():
    with database.get_session() as session:
        inst = session.query(DataDef).order_by(DataDef.datadef_id).all()
        return inst

def _get_dataproviders3(datadef_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(DataDefS3).filter(DataDefS3.datadef_id == datadef_id), session)

def _get_dataproviders3_query(datadef_id):
    with database.get_session() as session:
        return session.query(DataDefS3).filter(DataDefS3.datadef_id == datadef_id).one(), session



# Endpoint definitions
class DataProviderList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_dataproviders, _merge_dataprovider, _get_dataprovider_fields)


class DataProviderApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_dataprovider, _merge_dataprovider, _get_dataprovider_fields, "datadef_id")

    def get(self, datadef_id):
        inst = _get_dataprovider(datadef_id)[0]

        dataprovider_dict = marshal(inst, _get_dataprovider_fields())

        if inst.dataprovider_id == 1:
            try:
                # Try to get details off the details instance, otherwise only the main cloud info is returned
                details_inst = _get_dataproviders3_query(inst.datadef_id)[0]
                details_dict = marshal(details_inst, _get_s3_fields())
                dataprovider_dict.update(details_dict)
            except (TypeError, NoResultFound):
                pass

        return json_response(dataprovider_dict)


class DataProviderApiDetails(restful.Resource):

    def post(self, cloud_id, action):
        action = action.lower()

        if action == "createsnapshot":
            # Build snapshot here...
            pass
        elif action == "startinstance":
            pass


# Registering all ressources/endpoints served by this script
api_restful.add_resource(DataProviderList, api_prefix)
api_restful.add_resource(DataProviderApi, api_prefix + "/<int:datadef_id>")
api_restful.add_resource(DataProviderApiDetails, api_prefix + "/<int:datadef_id>/<string:action>")
