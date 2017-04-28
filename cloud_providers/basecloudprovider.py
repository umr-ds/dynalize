'''
Created on 11.03.2015

@author: PUM
'''

from abc import ABCMeta, abstractmethod

class BaseCloudProvider(metaclass=ABCMeta):

    @abstractmethod
    def initial_deployment(self):
        ''' This methods should fire up a virtual machine, install docker and the client and returns the instance
        '''
        pass

    @abstractmethod
    def start_instance(self):
        pass

    @abstractmethod
    def launch_instance(self):
        pass

    @abstractmethod
    def stop_instance(self):
        pass

    @abstractmethod
    def terminate_instance(self):
        pass

    @abstractmethod
    def instance_status(self):
        pass

    @abstractmethod
    def remove_snapshot(self):
        pass

    @abstractmethod
    def remove_image(self):
        pass
