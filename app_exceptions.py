'''
@author: PUM
'''

class UnknownCloudException(Exception):
    pass

class DockerBuildException(Exception):
    def __init__(self, build_log):
        self.build_log = build_log

class InvalidSnapshotException(Exception):
    pass

class InvalidInstanceException(Exception):
    pass
