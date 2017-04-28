'''
@summary: Parsing of commandline arguments
@author: PUM
'''
import argparse
import config
import requests
import log

parser = argparse.ArgumentParser(prog=config.app_name, description=config.app_description)

def _add_commandline_arguments():
    parser.add_argument("-v", "--version", help="Print version information.", action="version", version=_get_version())
    parser.add_argument("-d", "--debug", help="Enable debug output.", action="store_true", default=config.debug)

    # REST
    parser.add_argument("-p", "--port", help="Port the webservice is listening to.", type=int, default=config.bind_port, dest="port")
    parser.add_argument("-b", "--bind", help="Hostname the werbservice is bind to.", default=config.bind_host, dest="host", metavar="HOST")

    # Master
    parser.add_argument("-m", "--master", help="Launch master daemon instead of slave daemon.", action="store_true", default=config.master_daemon)
    parser.add_argument("-ms", "--master-scheduling-algo", help="Set an algorithm used to distribute the tasks to the worker. 'History' will try to send a task to a worker which previously ran the same file. 'Random' will let celery decide how to distribute the tasks.",
                        dest="master-scheduling-algo", default=config.master_scheduling_algo, choices=['history', 'random'])

    # Database
    parser.add_argument("--init-data", help="Inserts inital data into a newly created database.", action="store_true", dest="init-data", default=config.insert_inital_data)
    parser.add_argument("--database", help="Connection-String for SQLAlchemy.", dest="connstr", metavar="CONN_STR", default=config.database_connection_str)

    # Cache options
    parser.add_argument("--empty-cache", help="Deletes the contents of the local cache, in case there is any.", action="store_true", dest="empty-cache", default=config.cacher_empty_cache)
    parser.add_argument("--cache-threads", help="Defines how many concurrent cache threads should be running.", dest="cache_threads", default=config.cacher_threads)

    # Worker options
    parser.add_argument("--docker-url", help="Connection-String for Docker.", dest="dockerurl", metavar="URL", default=config.client_docker_url)
    parser.add_argument("--uds-path", help="Unix Domain Socket path for Worker.", dest="uds_path", default=config.client_uds_path)
    parser.add_argument("-q", "--queues", help="Queues which include tasks for this worker.", dest="queues", metavar="QUEUES", default=config.client_queues)
    parser.add_argument("-c", "--max-containers", help="Defines how many concurrent containers should be running.", dest="max_containers", default=config.client_threads)
    parser.add_argument("-u", "--user", help="Sets the username under which the celery worker will run.", dest="user", default=config.client_username)


    # S3 Deployment
    parser.add_argument("--s3-deployment", help="Start self-deployment to s3, outputs a temporary url and exits.", action="store_true", dest="s3-deployment", default=config.s3_deployment)
    parser.add_argument("--s3-deployment-bucket", help="Specifies the bucket used for s3 deployment.", dest="s3-deployment-bucket", metavar="BUCKET", default=config.s3_deployment_bucket)
    parser.add_argument("--s3-deployment-expire", help="Specifies the time the generated URL is valid in seconds.", dest="s3-deployment-expire", metavar="TIME", default=config.s3_deployment_expire)


def _parse_commandline_arguments(parameters=""):
    parsedArgs = {}

    parameter_args = vars(parser.parse_args(parameters.split()))
    commandline_args = vars(parser.parse_args())

    parsedArgs.update(parameter_args)
    parsedArgs.update(commandline_args)

    config.debug = parsedArgs["debug"]

    config.bind_port = parsedArgs["port"]
    config.bind_host = parsedArgs["host"]

    config.master_daemon = parsedArgs["master"]
    config.master_scheduling_algo = parsedArgs["master-scheduling-algo"]

    config.insert_inital_data = parsedArgs["init-data"]
    config.database_connection_str = parsedArgs["connstr"]

    config.cacher_empty_cache = parsedArgs["empty-cache"]
    config.cacher_processes = parsedArgs["cache_threads"]

    config.client_docker_url = parsedArgs["dockerurl"]
    config.client_uds_path = parsedArgs["uds_path"]
    config.client_queues = parsedArgs["queues"]
    config.client_processes = parsedArgs["max_containers"]
    config.client_username = parsedArgs["user"]

    config.s3_deployment = parsedArgs["s3-deployment"]
    config.s3_deployment_bucket = parsedArgs["s3-deployment-bucket"]
    config.s3_deployment_expire = parsedArgs["s3-deployment-expire"]


def _get_version():
    return ("%s: Version %s" % (config.app_name, config.app_version))

def _get_ec2_userdata():
    ''' Checks if ec2 metadata contain userdata related to dynalize and use them to startup '''

    try:
        r = requests.get("http://localhost/latest/user-data")

        if r.status_code == 200:
            return r.json()['dynalize_parameter']
    except:
        logger = log.setup_logger(__name__)
        logger.error("Failed to get ec2 userdata")

    return ""


def setup_console():
    # Try to add the last git revision to the version-string
    config.add_git_rev_to_version()

    _add_commandline_arguments()
    _parse_commandline_arguments(_get_ec2_userdata())
    # Check if we need to set all loggers to debug mode
    config.update_debug_mode()

    # After setting up and parsing commandline arguments, make sure this is a valid config
    config.validate_config()
