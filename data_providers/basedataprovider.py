'''
Created on 26.02.2015

@author: PUM
'''
from abc import ABCMeta, abstractmethod

class BaseDataProvider(metaclass=ABCMeta):
    '''
    classdocs
    '''

    @abstractmethod
    def upload(self, source, destination_path, destination_filename):
        pass

    @abstractmethod
    def download(self, source, destination):
        pass

    @abstractmethod
    def upload_file(self, path, destination_path, destination_filename):
        pass

    @abstractmethod
    def download_file(self, source, path):
        pass

    @abstractmethod
    def get_files(self, path):
        pass

    @abstractmethod
    def get_hash(self, source):
        pass

    @staticmethod
    def dataprovider_by_name(name):
        import data_providers

        name = name.lower()

        if name.startswith("s3"):
            return data_providers.s3provider.S3DataProvider
        elif name.startswith("http"):
            return data_providers.httpprovider.HttpDataProvider
        elif name.startswith("git"):
            return data_providers.gitprovider.GitDataProvider
        else:
            raise ValueError("Unknown DataProvider")

    @staticmethod
    def dataprovider_by_model(model):
        import data_providers

        if model.dataprovider_id == 1:
            # S3
            s3_data = model.datadefs3_relation

            return data_providers.s3provider.S3DataProvider, {
                                                              'bucket_name' : s3_data.bucket_name,
                                                              'access_key' : s3_data.access_key,
                                                              'secret_key' : s3_data.secret_key
                                                              }
        elif model.dataprovider_id == 2:
            # HTTP
            return data_providers.httpprovider.HttpDataProvider, {}
        elif model.dataprovider_id == 3:
            # Git
            return data_providers.gitprovider.GitDataProvider, {}
        else:
            raise ValueError("Unknown DataProvider")

class DataProviderFile():
    def __init__(self, path, filename, fullpath):
        self.path = path
        self.filename = filename
        self.fullpath = fullpath

    def __repr__(self):
        return "<DataProviderFile(path='%s', filename='%s', fullpath='%s')>" \
            % (self.path, self.filename, self.fullpath)
