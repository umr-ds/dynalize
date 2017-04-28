'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String
from database import Base

class CloudProvider(Base):
    __tablename__ = 'cloudprovider'

    cloudprovider_id = Column(Integer, primary_key=True)
    name = Column(String)


    def __repr__(self):
        return "<CloudProvider(cloudprovider_id='%s', name='%s')>" % (self.cloudprovider_id, self.name)
