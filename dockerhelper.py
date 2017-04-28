'''
Parts are based on the efficiency-branch of docker-py. See https://github.com/docker/docker-py/blob/efficiency/docker/efficiency/ and https://github.com/docker/docker-py/issues/417

@author: PUM
'''
import json
import re
import atexit
import log

logger = log.setup_logger(__name__)
build_success_re = r'^Successfully built ([a-f0-9]+)\n$'

def safe_start(client, *args, **kwargs):
    def container_cleanup(client, cid):
        client.stop(cid)

    client.start(*args, **kwargs)
    if len(args) == 1:
        atexit.register(container_cleanup, client, args[0])
    else:
        atexit.register(container_cleanup, client, kwargs['container'])


def get_build_id(build_result, discard_logs=False):
    """ **Params:**
        * `build_result` is a python generator returned by `Client.build`
        * `discard_logs` (bool, default=False). If True, log lines will
          be discarded after they're processed. Limits memory footprint.
        **Returns** tuple:
            1. Image ID if found, None otherwise
            2. List of log lines
    """
    parsed_lines = []
    image_id = None
    for line in build_result:
        try:
            parsed_line = json.loads(line.decode("utf-8")).get('stream', '')
            logger.debug("Build-Stream: '%s'" % parsed_line.rstrip())
            if not discard_logs:
                parsed_lines.append(parsed_line)
            match = re.match(build_success_re, parsed_line)
            if match:
                image_id = match.group(1)
        except ValueError:
            # sometimes all the data is sent on a single line
            # This ONLY works because every line is formatted as
            # {"stream": STRING}
            lines = re.findall('{\s*"stream"\s*:\s*"[^"]*"\s*}', line)
            return get_build_id(lines, discard_logs)

    return image_id, parsed_lines
