'''
@author: PUM
'''
from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from database.model.layer import Layer
from database.model.cloudprovider import CloudProvider
from database.model.instance import Instance
from database.model.job import Job


class CloudDef(Base):
    '''
    Stores general cloud settings, relevant to all clouds
    '''
    __tablename__ = 'clouddef'

    clouddef_id = Column(Integer, primary_key=True)
    name = Column(String)
    cloudprovider_id = Column(Integer, ForeignKey("cloudprovider.cloudprovider_id"), nullable=False)
    virtual_device_layer_id = Column(Integer, ForeignKey("layer.layer_id"))
    test_layer_id = Column(Integer, ForeignKey("layer.layer_id"))
    snapshot_id = Column(String)
    snapshot_image_id = Column(String)
    client_startup_parameters = Column(String, nullable=False)
    #status = Column(Integer)

    virtual_device_layer_relation = relationship(lambda: Layer, foreign_keys=[virtual_device_layer_id])
    test_layer_relation = relationship(lambda: Layer, foreign_keys=[test_layer_id])
    cloudtype_relation = relationship(lambda: CloudProvider)

    instance_relation = relationship(lambda: Instance, backref="clouddef", cascade="all,delete")
    clouddefec2_relation = relationship(lambda: CloudDefEc2, backref="clouddef", uselist=False, cascade="all,delete")
    job_relation = relationship(lambda: Job, backref="clouddef", cascade="all,delete")


    def __repr__(self):
        return "<CloudDef(clouddef_id='%s', name='%s', cloudtype_id='%s', virtual_device_layer_id='%s', test_layer_id='%s', snapshot_id='%s', snapshot_image_id='%s', client_startup_parameters='%s')>" \
            % (self.clouddef_id, self.name, self.cloudprovider_id, self.virtual_device_layer_id, self.test_layer_id, self.snapshot_id, self.snapshot_image_id, self.client_startup_parameters)

class CloudDefEc2(Base):
    '''
    Stores EC2 specific settings in addition to general cloud settings
    '''
    __tablename__ = 'clouddefec2'

    # IDs
    clouddefec2_id = Column(Integer, primary_key=True)
    clouddef_id = Column(Integer, ForeignKey("clouddef.clouddef_id"), nullable=False)

    # EC2 specific columns
    base_ami = Column(String)
    keypair = Column(String)
    security_group = Column(String)
    subnet = Column(String)
    access_key = Column(String)
    secret_key = Column(String)


    def __repr__(self):
        return "<CloudDefEc2(clouddefec2_id='%s', clouddef_id='%s', base_ami='%s', keypair='%s', security_group='%s', subnet='%s', access_key='%s', secret_key='%s')>" \
            % (self.clouddefec2_id, self.clouddef_id, self.base_ami, self.keypair, self.security_group, self.subnet, self.access_key, self.secret_key)
