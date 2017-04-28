'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime, Numeric

from datetime import datetime

class Task(Base):
    '''
    classdocs
    '''
    __tablename__ = 'task'

    # IDs
    task_id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job.job_id"), nullable=False)

    # Task specific columns
    filename = Column(String)
    backend_id = Column(String) # Internal Task-ID used by the backend (eg Celery)
    worker_hostname = Column(String) # Hostname of worker which the task got scheduled to.

    # Result specific columns
    created_on = Column(DateTime, default=datetime.now)
    completed = Column(Boolean)
    output = Column(Text)
    build_logs = Column(Text)
    exception = Column(Text)
    traceback = Column(Text)
    exit_code = Column(Integer)
    duration = Column(Numeric)


    def __repr__(self):
        return "<Task(task_id='%s', job_id='%s', filename='%s', created_on='%s', completed='%s', output='%s', build_logs='%s', exception='%s', traceback='%s', backend_id='%s', worker_hostname='%s', elapsed_time='%s')>" \
            % (self.task_id, self.job_id, self.filename, self.created_on, self.completed, self.output, self.build_logs, self.exception, self.traceback, self.backend_id, self.worker_hostname, self.elapsed_time)
