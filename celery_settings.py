'''
@author: PUM
'''

CELERY_RESULT_BACKEND='rpc'
BROKER_URL='amqp://dynalize:dynalize@localhost:6555/dynalize_vhost'

CELERY_ROUTES = {
                 "celerycontrol.add_task_result": {"queue": "results"},
                 "celerycontrol.add_task_uds": {"queue": "tasks"}
                 }
