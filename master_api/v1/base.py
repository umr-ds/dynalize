from flask import request
from flask.ext import restful
from flask.ext.restful import marshal
from common_api.json import  json_success, json_response
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask_restful import abort

class ListApi(restful.Resource):
    def __init__(self, get_all_func, merge_func, list_field_func):
        self.get_all_func = get_all_func
        self.merge_func = merge_func
        self.list_field_func = list_field_func
        
    def get(self):
        inst = self.get_all_func()
           
        return json_response(marshal(inst, self.list_field_func()))
    
    def post(self):
        json_data = request.get_json()

        return self.merge_func(json_data)

class DetailsApi(restful.Resource):
    def __init__(self, get_func, merge_func, details_field_func, id_name):
        self.get_func = get_func
        self.merge_func = merge_func
        self.details_field_func = details_field_func
        self.id_name = id_name
        
    def get(self, **kwargs):
        req_id = kwargs[self.id_name]
        inst = self.get_func(req_id)[0]

        return json_response(marshal(inst, self.details_field_func()))
      
    def put(self, **kwargs):
        req_id = kwargs[self.id_name]
        json_data = request.get_json()
        
        return self.merge_func(json_data, req_id)
    
    def delete(self, **kwargs):
        req_id = kwargs[self.id_name]
        inst, session = self.get_func(req_id)
        
        session.delete(inst)
        session.commit()

        return json_success()
    
def get_single_record(inst, session):
    # This way max. 1 query is send to the DB. Using count() will issue a query for each call
    try: 
        return inst.one(), session
    except NoResultFound:
        # Nothing found
        abort(404)
    except MultipleResultsFound:
        # Should not happen, something's wrong with the primary key
        abort(500)
    
