'''
Created on 02.03.2015

@author: PUM
'''
from flask import jsonify

def json_status(success, status_code=200, error_description='', url=''):
    response = jsonify(json_response({'success': success, 'error': error_description, 'url': url}))
    response.status_code = status_code
    return response


def json_success():
    return json_status(True)

def json_response(data):
    ''' Due to security-problems with JSONArrays (see http://flask.pocoo.org/docs/0.10/security/) make sure everything is packed as an JSONObject. Although Flask will make sure that no JSONArray as top-level element is sent to the client, we want to have a common structure for all requests.'''
    return {'data': data}
