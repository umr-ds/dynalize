'''
Created on 05.03.2015

@author: PUM
'''
from flask_restful.fields import Url
from flask.ext.restful import fields

class BpUrl(Url):
    '''Takes an blueprint-name and a flask-restful resource and returns the correct string to resolve the corresponding url'''
    def __init__(self, api_restful=None, resource=None, **kwargs):
        if api_restful.blueprint is not None:
            super().__init__("{0}.{1}".format(api_restful.blueprint.name, resource.endpoint), **kwargs)
        else:
            super().__init__("{0}".format(resource.endpoint), **kwargs)


class CustomDateTime(fields.DateTime):
    def __init__(self, dt_format="%d.%m.%Y %H:%M:%S"):
        fields.DateTime.__init__(self)

        self.dt_format = dt_format


    def format(self, value):
        return value.strftime(self.dt_format)
