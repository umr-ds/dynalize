'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String, Text
from database import Base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.sql.sqltypes import DateTime

class Layer(Base):
    '''
    classdocs
    '''
    __tablename__ = 'layer'

    layer_id = Column(Integer, primary_key=True)
    name = Column(String)
    tag = Column(String)
    content = Column(Text)
    modified_on = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Use a string to reference the ForeignKey instead of the column object
    # this way the order is not important when working with multiple modules
    # see http://docs.sqlalchemy.org/en/rel_0_9/core/constraints.html
    parent_id = Column(Integer, ForeignKey("layer.layer_id"))

    parent = relationship(lambda: Layer)

    def __repr__(self):
        return "<Layer(layer_id='%s', name='%s', tag='%s', content='%s', parent_id='%s')>" % (self.layer_id, self.name, self.tag, self.content, self.parent_id)
