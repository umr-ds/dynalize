'''
@author: PUM
'''
from data_providers.basedataprovider import BaseDataProvider
from git import Repo

class GitDataProvider(BaseDataProvider):
    '''
    classdocs
    '''
    def __init__(self, *args, **kwargs):
        pass

    def download(self, source, destination):
        # Problem: Need to pull complete repo to iterate through files -> will not scale through multiple clients
        repo = Repo.init("temp")
        origin = repo.create_remote('origin', source)
        origin.fetch()
        origin.pull()

        tree = repo.heads.master.commit.tree

        for entry in tree:
            print(entry)


    def upload(self, source, destination):
        BaseDataProvider.upload(self, source, destination)
