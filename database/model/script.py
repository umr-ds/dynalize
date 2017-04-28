'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String, Text
from database import Base
import datetime
from sqlalchemy.sql.sqltypes import DateTime

class Script(Base):
    '''
    classdocs
    '''
    __tablename__ = 'script'

    script_id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(Text)
    modified_on = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return "<Script(script_id='%s', name='%s', content='%s')>" % (self.script_id, self.name, self.content)
