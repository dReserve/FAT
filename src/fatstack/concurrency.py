import threading, asyncio


class AsyncThread(threading.Thread):
    def __init__(self):
        super().__init__()
        # self.done_init = threading.Event()
        self.loop = None
        # self.tid = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # self.tid = threading.current_thread()
        # self.loop.call_soon(self.done_init.set)
        self.register_tasks()
        self.loop.run_forever()

    def register_tasks():
        """
        Initializes the event loop. This must be defined by the child classes.
        """
        pass

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
