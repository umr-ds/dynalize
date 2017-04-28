'''
End-user python library - exposes functions to support the development of test scripts in python.
Currently implemented functionality:
 - Cache-handling (wait until the cache is ready)
 - Retrieve information of the current task (name, id, etc.)

@author: PUM
'''
import os
import time
import textwrap


def wait_for_data_ready():
    ''' Waits until the cache signals it's ready. Returns immediately if cache-task already finished.'''
    ready_file = os.path.join(get_task_input_path(), "data_ready")

    while not os.path.isfile(ready_file):
        time.sleep(0.1)


def get_task_id():
    return os.environ.get('TASK_ID')

def get_task_name():
    return os.environ.get('TASK_NAME')

def get_task_file():
    return os.environ.get('TASK_FILE')

def get_task_input_path():
    return os.environ.get('TASK_INPUT_PATH')

def get_task_output_path():
    return os.environ.get('TASK_OUTPUT_PATH')

def print_task_information():
    output = textwrap.dedent('''
    ID: %(task_id)s
    Name: %(task_name)s
    File: %(task_file)s
    Input-path: %(input_path)s
    Output-path: %(output_path)s
    ''')

    print(output % {'task_id' : get_task_id(),
                    'task_name' : get_task_name(),
                    'task_file' : get_task_file(),
                    'input_path' : get_task_input_path(),
                    'output_path' : get_task_output_path()})
