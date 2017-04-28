'''
@author: PUM
'''
import asyncio
import config
import log

logger = log.setup_logger(__name__)

class UnixDomainSocketClient():
    '''      '''

    def send_json_task(self, json_task):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._send_json_task_worker(json_task, loop))

    @asyncio.coroutine
    def _send_json_task_worker(self, json_task, loop):
        logger.debug("Opening connection to unix-domain-socket at '%s'" % config.client_uds_path)
        _, writer = yield from asyncio.open_unix_connection(config.client_uds_path)

        writer.write(json_task.encode("utf-8"))
        writer.close()
