'''
@summary: This module stores settings globally and allows basic verification
@author: PUM
'''
import log
import logging
import subprocess

# Some fundamental application settings - shouldn't be editable via commandline
app_name = "Dynalize"
app_description = "DynalizeDesc"
app_version = "0.1"

# Debug-mode
debug = False

# bind options
bind_port = 443
bind_host = "0.0.0.0"

# Master / Worker
master_daemon = False

# cache options
cacher_directory = "cacher_data"
cacher_threads = 2
cacher_empty_cache = False

# databse options
insert_inital_data = False
database_connection_str = 'sqlite:///test.db'

# s3 deployment options
s3_deployment = False
s3_deployment_expire = 600
s3_deployment_bucket = 'umr_test'

# Master options
master_scheduling_algo = "history"

# Worker options
client_threads = 2
client_docker_url = None
client_uds_path = "/dev/dynalize"
client_queues = ""
client_username = "ubuntu"

def validate_config():
    ''' Validates currently stored config-values'''
    # Don't do this at module level as we cannot guarantee that all config options used by setup_logger are already setup
    logger = log.setup_logger(__name__)

    if bind_port <= 0:
        raise ValueError("Port must be a positive, non-zero integer")
    elif bind_port < 1024:
        logger.warning("Port should not be in the range of well-known ports (0-1023)")


def update_debug_mode():
    if not debug:
        return

    # Don't do this at module level as we cannot guarantee that all config options used by setup_logger are already setup
    logger = log.setup_logger(__name__)

    # Check debug setting and change any already existing logger to DEBUG level.
    # Any logger created afterwards will be set to DEBUG already.
    created_loggers = logging.getLogger().manager.loggerDict

    for temp_logger_name, temp_logger in created_loggers.items():
        logger.debug("Changing loglevel of '%s' to DEBUG", temp_logger_name)
        try:
            temp_logger.setLevel(logging.DEBUG)
        except AttributeError:
            pass

def add_git_rev_to_version():
    global app_version

    try:
        git_rev = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode("utf-8").strip()

        # This obviuosly only works if git installed and Dynalize is run off a git repo, so make sure we really get a revision
        if len(git_rev) == 7:
            app_version = app_version + "-" + git_rev
    except:
        # This is really unimportant and no problem if it fails
        pass
