'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from database.model.dataprovider import DataProvider


class DataDef(Base):
    '''
    Stores general cloud settings, relevant to all clouds
    '''
    __tablename__ = 'datadef'

    datadef_id = Column(Integer, primary_key=True)
    name = Column(String)
    dataprovider_id = Column(Integer, ForeignKey("dataprovider.dataprovider_id"), nullable=False)

    source = Column(String)
    source_path_filter = Column(String)
    source_filename_filter = Column(String)

    destination = Column(String)

    dataprovider_relation = relationship(lambda: DataProvider)
    datadefs3_relation = relationship(lambda: DataDefS3, backref="datadef", uselist=False, cascade="all,delete")

    def __repr__(self):
        return "<DataDef(datadef_id='%s', name='%s', dataprovider_id='%s', source='%s', source_path_filter='%s', source_filename_filter='%s', destination='%s')>" \
            % (self.datadef_id, self.name, self.dataprovider_id, self.source, self.source_path_filter, self.source_filename_filter, self.destination)

class DataDefS3(Base):
    '''
    Stores EC2 specific settings in addition to general cloud settings
    '''
    __tablename__ = 'datadefs3'

    # IDs
    datadefs3_id = Column(Integer, primary_key=True)
    datadef_id = Column(Integer, ForeignKey("datadef.datadef_id"), nullable=False)

    # EC2 specific columns
    bucket_name = Column(String)
    access_key = Column(String)
    secret_key = Column(String)


    def __repr__(self):
        return "<DataDefS3(datadefs3_id='%s', datadef_id='%s', bucket_name='%s', access_key='%s', secret_key='%s')>" \
            % (self.datadefs3_id, self.datadef_id, self.bucket_name, self.access_key, self.secret_key)
