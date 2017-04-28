'''
@author: PUM
'''

import asyncio
import atexit
import os
import config
import log

logger = log.setup_logger(__name__)

class UnixDomainSocketServer():

    def __init__(self, scheduler):
        '''        Constructor        '''
        self.scheduler = scheduler

        atexit.register(self.cleanup)

        try:
            os.unlink(config.client_uds_path)
        except:
            pass

        self.loop = asyncio.get_event_loop()
        self.server_handler = asyncio.start_unix_server(self.handle_client, config.client_uds_path)
        self.server = self.loop.run_until_complete(self.server_handler)

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass


    def cleanup(self):
        logger.debug("Shutting down. Starting cleanup.")

        try:
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()
            os.unlink(config.client_uds_path)
        except:
            pass

        logger.debug("Cleanup finished")

    def handle_client(self, reader, writer):
        data = yield from reader.read()
        message = data.decode("utf-8")

        logger.debug("Received '%s'" % message)

        self.scheduler.add_task_from_json(message)
