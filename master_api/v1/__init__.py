'''
Created on 02.03.2015

@author: PUM
'''
from flask.blueprints import Blueprint
from flask.ext import restful


api = Blueprint('apiv1', __name__)
api_restful = restful.Api(api)


from . import script
from . import layer
from master_api.v1 import clouddef
from master_api.v1 import cloudprovider
from . import job
from . import instance
from master_api.v1 import datadef
from master_api.v1 import dataprovider
from . import task
from . import worker
