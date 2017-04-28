'''
@author: PUM
'''
import os
import zipfile
import tempfile
import config
import log
import textwrap
from data_providers import s3provider
import json

logger = log.setup_logger(__name__)
excludes = ['__pycache__', 'cacher_data', '.git']

def zip_directory(path, zip_file):
    for root, dirs, files in os.walk(path):
        dirs[:] = [x for x in dirs if x not in excludes]

        for file in files:
            zip_file.write(os.path.join(root, file))

def get_zip_file():
    # Create zip file for deployment
    spooled_tempfile = tempfile.SpooledTemporaryFile()
    zip_file = zipfile.ZipFile(spooled_tempfile, 'w', zipfile.ZIP_DEFLATED)
    zip_directory('./', zip_file)
    zip_file.close()

    spooled_tempfile.seek(0)
    return spooled_tempfile


def create_deploy_json_file(virtual_device_layer, test_layer):
    dic = {
            'virtual_device_layer' : {
                                      'content' : virtual_device_layer.content,
                                      'tag' : virtual_device_layer.tag
                                      },
            'test_layer' : {
                            'content' : test_layer.content,
                            'tag' : test_layer.tag
                            }
            }

    with open("deploy.json", "w") as f:
        json.dump(dic, f)

def remove_deploy_json_file():
    if os.path.isfile("deploy.json"):
        os.remove("deploy.json")


def selfdeploy_to_s3(bucket_name=config.s3_deployment_bucket, expires_in_sec=config.s3_deployment_expire):
    ''' Creates a zip file containing the whole application, uploads it to S3 and returns a temporary url '''
    s3 = s3provider.S3DataProvider(bucket_name)
    spooled_tempfile = get_zip_file()

    # Should we use a hash here?
    key_name = config.app_name + config.app_version + ".zip"

    s3.upload(spooled_tempfile, "", key_name)

    # Make sure the tempfile is closed and therefore removed from the system
    spooled_tempfile.close()

    return s3.generate_temporary_url(key_name, expires_in_sec)

def manual_s3_deployment():
    output =  textwrap.dedent('''
    %(app_name)s (Version %(app_version)s) was deployed to Amazon S3:
    Bucket: %(bucket_name)s
    URL: %(url)s

    Note: The URL is a temporary one and is only valid the next %(expiry)s seconds.
    ''')

    logger.debug("Starting self-deployment to s3 bucket '%s'" % config.s3_deployment_bucket)
    temp_url = selfdeploy_to_s3(config.s3_deployment_bucket)
    logger.debug("Finsihed self-deployment to s3")

    print(output % {'app_name' : config.app_name,
                    'app_version' : config.app_version,
                    'bucket_name' : config.s3_deployment_bucket,
                    'url' : temp_url,
                    'expiry' : config.s3_deployment_expire
                    })
