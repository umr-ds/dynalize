'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from database.model.layer import Layer
from database.model.script import Script
from database.model.task import Task
from database.model.datadef import DataDef

class Job(Base):
    '''
    classdocs
    '''
    __tablename__ = 'job'

    # IDs
    job_id = Column(Integer, primary_key=True)
    clouddef_id = Column(Integer, ForeignKey("clouddef.clouddef_id"), nullable=False)
    run_layer_id = Column(Integer, ForeignKey("layer.layer_id"))
    script_id = Column(Integer, ForeignKey("script.script_id"))
    source_datadef_id = Column(Integer, ForeignKey("datadef.datadef_id"))
    destination_datadef_id = Column(Integer, ForeignKey("datadef.datadef_id"))

    # Job specific columns
    name = Column(String)
    task_timeout = Column(Integer)


    run_relation = relationship(lambda: Layer, foreign_keys=[run_layer_id])
    script_relation = relationship(lambda: Script, foreign_keys=[script_id])

    source_datadef_relation = relationship(lambda: DataDef, foreign_keys=[source_datadef_id])
    destination_datadef_relation = relationship(lambda: DataDef, foreign_keys=[destination_datadef_id])

    task_relation = relationship(lambda: Task, backref="job", cascade="all,delete")

    def __repr__(self):
        return "<Job(job_id='%s', clouddef_id='%s', run_layer_id='%s', script_id='%s', name='%s', task_timeout='%s')>" \
            % (self.job_id, self.clouddef_id, self.run_layer_id, self.script_id, self.name, self.task_timeout)
