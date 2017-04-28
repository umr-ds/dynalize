'''
@author: PUM
'''
from data_providers.basedataprovider import BaseDataProvider
import requests
import shutil

class HttpDataProvider(BaseDataProvider):
    ''' Provides a simple interface for downloading/uploading files through the http protocol. '''

    # see http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file
    def upload(self, source, destination, multipart_encoding_upload=True):
        if multipart_encoding_upload:
            files = {'file': open(source, 'rb')}

            requests.post(destination, files=files)
        else:
            with open(source, 'rb') as fd:
                requests.post(destination, data=fd)


    def download(self, source, destination):
        r = requests.get(source, stream=True)
        if r.status_code == 200:
            with open(destination, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)


    def get_files(self):
        return []

    def get_hash(self, source):
        return None
