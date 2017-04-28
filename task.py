'''
@author: PUM
'''
import json
import socket
from json.encoder import JSONEncoder

class JsonSerializableEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, JsonSerializable):
            return o.__dict__

        return JSONEncoder.default(self, o)

class JsonSerializable():
    def to_json(self):
        return json.dumps(self.__dict__, cls=JsonSerializableEncoder)


class TaskResult():
    def __init__(self, task_id):
        self.task_id = task_id

        self.completed = False
        self.output = None
        self.build_logs = []
        self.exception = None
        self.traceback = None
        self.exit_code = None
        self.duration = None

        self.hostname = socket.gethostname()

class TaskDataProvider(JsonSerializable):
    def __init__(self, data_provider_type, source, destination, kwargs):
        self.data_provider_type = data_provider_type
        self.source = source
        self.destination = destination
        self.kwargs = kwargs

class TaskLayer(JsonSerializable):
    def __init__(self, content, tag):
        self.content = content
        self.tag = tag

class TaskScript(JsonSerializable):
    def __init__(self, content, name):
        self.content = content
        self.name = name

class Task(JsonSerializable):
    def __init__(self, task_id, name, source_data_def, destination_data_def, virtual_device_layer, test_layer, run_layer, script, task_file, timeout, script_data_def, **kwargs):
        self.task_id = task_id
        self.name = name
        self.source_data_def = source_data_def
        self.destination_data_def = destination_data_def
        self.virtual_device_layer = virtual_device_layer
        self.test_layer = test_layer
        self.run_layer = run_layer
        self.script = script
        self.task_file = task_file
        self.timeout = timeout
        self.kwargs = kwargs
        self.script_data_def = script_data_def

        self.finished = False
        self.started = False

    # As this class will be send over a unix domain socket, we need to have serialization options here
    @classmethod
    def from_json(cls, json_str):
        json_parsed = json.loads(json_str)
        return cls(json_parsed['task_id'], json_parsed['name'], json_parsed['source_data_def'], json_parsed['destination_data_def'], json_parsed['virtual_device_layer'], json_parsed['test_layer'], json_parsed['run_layer'], json_parsed['script'], json_parsed['task_file'], json_parsed["timeout"], json_parsed["script_data_def"])

    @classmethod
    def from_json_deployment(cls, json_str):
        json_parsed = json.loads(json_str)
        return cls(0, "Deployment Task", None, None, json_parsed['virtual_device_layer'], json_parsed['test_layer'], None, None, None, None, None)
