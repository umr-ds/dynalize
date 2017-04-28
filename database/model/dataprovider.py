'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String
from database import Base

class DataProvider(Base):
    __tablename__ = 'dataprovider'

    dataprovider_id = Column(Integer, primary_key=True)
    name = Column(String)


    def __repr__(self):
        return "<DataProvider(dataprovider_id='%s', name='%s')>" % (self.dataprovider_id, self.name)
