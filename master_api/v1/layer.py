'''
@author: PUM
'''
import database

from . import api_restful, base
from flask.ext import restful
from flask.ext.restful import marshal, fields
from database.model.layer import Layer
from common_api.json import json_status, json_response
from common_api.customfields import BpUrl

# Prefix for all API calls served by this script
api_prefix = "/layer"

# Marhsalling information for datastructures used by this script
def _get_layer_fields():
    details_fields = _get_layer_details_fields()
    del details_fields['content']
    return details_fields

def _get_layer_details_fields():
    return {
            'layer_id' : fields.Integer,
            'name' : fields.String,
            'tag' : fields.String,
            'content' : fields.String,
            'parent_id' : fields.Integer(default=None), # Make sure we actually get "null" and not "0"
            'modified_on' : fields.DateTime(dt_format='iso8601'),
            'uri' : BpUrl(api_restful, LayerApi, absolute=True)
            }

def _get_layer(layer_id):
    with database.get_session() as session:
        return base.get_single_record(session.query(Layer).filter(Layer.layer_id == layer_id), session)

def _get_all_layers():
    with database.get_session() as session:
        inst = session.query(Layer).order_by(Layer.name).all()
        return inst

def _merge_layer(json_data, layer_id=None):
    if json_data is None or not 'name' in json_data or not 'content' in json_data:
        return json_status(False, 400, "Missing required parameters")

    with database.get_session() as session:
        new_layer = Layer(
                          layer_id  = layer_id,
                          name      = json_data.get('name'),
                          content   = json_data.get('content'),
                          tag       = json_data.get('tag', None),
                          parent_id = json_data.get('parent_id', None)
                          )

        if new_layer.parent_id == "0":
            new_layer.parent_id = None

        # Merge will automatically add a new instance if the primary key does not already exist
        new_layer = session.merge(new_layer)
        session.commit()

        return json_status(True, url=api_restful.url_for(LayerApi, layer_id=new_layer.layer_id))

def _get_layer_tree(layer_id):
    lstLayers = list()

    currentLayer = _get_layer(layer_id)[0]

    # Get first content
    lstLayers.insert(0, currentLayer)

    while currentLayer.parent_id is not None:
        currentLayer = _get_layer(currentLayer.parent_id)[0]
        lstLayers.insert(0, currentLayer)

    return lstLayers

# Endpoint definitions
class LayerList(base.ListApi):
    def __init__(self):
        base.ListApi.__init__(self, _get_all_layers, _merge_layer, _get_layer_fields)


class LayerApi(base.DetailsApi):
    def __init__(self):
        base.DetailsApi.__init__(self, _get_layer, _merge_layer, _get_layer_details_fields, "layer_id")

class LayerApiDetails(restful.Resource):
    def get(self, layer_id, action):
        action = action.lower()

        if action == "dockerfile":
            layer_tree = _get_layer_tree(layer_id)

            # Return concatenated string of all contents
            return json_response('\n'.join([l.content for l in layer_tree]))
        elif action == "tree":
            layer_tree = _get_layer_tree(layer_id)

            return json_response(marshal(layer_tree, _get_layer_fields()))
        elif action == "tree_full":
            layer_tree = _get_layer_tree(layer_id)

            return json_response(marshal(layer_tree, _get_layer_details_fields()))

# Registering all ressources/endpoints served by this script
api_restful.add_resource(LayerList, api_prefix)
api_restful.add_resource(LayerApi, api_prefix + "/<int:layer_id>")
api_restful.add_resource(LayerApiDetails, api_prefix + "/<int:layer_id>/<string:action>")
