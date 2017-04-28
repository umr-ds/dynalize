'''
@author: PUM
'''
from data_providers.basedataprovider import BaseDataProvider, DataProviderFile
import boto
import hashlib
import log
import os

logger = log.setup_logger(__name__)

class S3DataProvider(BaseDataProvider):
    ''' Provides a simple interface for downloading/uploading files from/to amazon s3. '''

    def __init__(self, bucket_name, access_key=None, secret_key=None):
        ''' If no aws-credentials specified, boto will use aws-cred. defined in environment vars or config files. See http://boto.readthedocs.org/en/latest/boto_config_tut.html '''
        self.access_key = access_key
        self.secret_key = secret_key

        # Boto treats an empty string as an passed credential. To workaround a potential wrong database entry, make sure we use None in this case
        if self.access_key == '': self.access_key = None
        if self.secret_key == '': self.secret_key = None

        self.bucket_name = bucket_name

        self.conn = None
        self.bucket = None

    def _get_connection(self):
        if self.conn is None:
            self.conn = boto.connect_s3(self.access_key, self.secret_key)
            self.bucket = self.conn.get_bucket(self.bucket_name)

        return self.conn, self.bucket

    def get_hash(self, key_name):
        ''' S3 provides a MD5 hash linked to each object. Returns the MD5 hash in case the key exists and None otherwise '''
        bucket = self._get_connection()[1]

        key = bucket.get_key(key_name)

        if key is not None:
            return key.etag.replace("\"", "").lower()

        return None


    def upload(self, source, destination_path, destination_filename):
        '''
        Uploads a file to a specified s3 bucket. Source is a file-like object. Object is not closed afterwards!

        :param destination_path: Represents the prefix of the file in s3.
        :param destination_filename: Represents the filename of the file in s3 (destination_path is prepended to the filename)
        '''
        bucket = self._get_connection()[1]

        # Make sure a path ends with a "/"
        if len(destination_path) > 0 and destination_path[-1] != "/":
            destination_path += "/"

        key_name = destination_path + destination_filename

        md5_server = self.get_hash(key_name)

        # Check if file is already present on server to avoid unnecessary uploads
        if md5_server is not None:
            md5_local = hashlib.md5(source.read()).hexdigest().lower()

            if md5_local == md5_server:
                logger.debug("File '%s' in bucket '%s' matches local file, skipping upload" % (key_name, self.bucket_name))
                return

            # Reset position of local file
            source.seek(0)

        logger.debug("File '%s' in bucket '%s' does not exist or is different from local file, starting upload" % (key_name, self.bucket_name))

        key = bucket.new_key(key_name)
        key.set_contents_from_file(source)


    def upload_file(self, path, destination_path, destination_filename):
        with open(path, "rb") as f:
            self.upload(f, destination_path, destination_filename)


    def download(self, key_name, destination):
        ''' Downloads a file from s3 bucket to a file-like object or as a file to the file-system.'''
        bucket = self._get_connection()[1]

        key = bucket.get_key(key_name)
        key.get_contents_to_file(destination)

    def download_file(self, source, path):
        # See boto implementation
        try:
            with open(path, "wb") as f:
                self.download(source, f)
        except:
            # Make sure we don't leave a empty file behind in case a exception occurs
            os.remove(path)
            raise

    def get_files(self, path, **kwargs):
        bucket = self._get_connection()[1]

        # Ignore "directory-like" keys and create a DataProviderFile obj for each file
        return [DataProviderFile(os.path.dirname(x.name), os.path.basename(x.name), x.name) for x in bucket.list(path, **kwargs) if not x.name.endswith("/")]


    def generate_temporary_url(self, key_name, expires_in_secs, method="GET"):
        ''' Generates a temporary url to a specified file/key in s3 which expires after the set time.'''
        conn = self._get_connection()[0]
        return conn.generate_url(expires_in_secs, method, self.bucket_name, key_name)



def s3_test():
    a = S3DataProvider("umr_test")
    a.download_file("bootstrap-3.3.2-dist.zip", "bootstrap-3.3.2-dist.zip")
    for f in a.get_files(""):
        print(f)
