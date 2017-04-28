'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
import datetime

class Instance(Base):

    __tablename__ = 'instance'

    instance_id = Column(Integer, primary_key=True)
    clouddef_id = Column(Integer, ForeignKey("clouddef.clouddef_id"))

    hostname = Column(String)
    comment = Column(String)
    provider_id = Column(String)
    provider_name = Column(String)
    status = Column(String)

    created_on = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return "<Instance(instance_id='%s', clouddef_id='%s', hostname='%s', provider_id='%s', provider_name='%s', created_on='%s', status='%s')>" % \
             (self.instance_id, self.clouddef_id, self.hostname, self.provider_id, self.provider_name, self.created_on, self.status)
