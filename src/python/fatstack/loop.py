import asyncio
import logging
import atexit
import signal
import functools

log = logging.getLogger("Loop")
loop = asyncio.get_event_loop()


def run_loop():
    atexit.register(exit_loop, 'Exiting.')
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                functools.partial(halt_by_signal,
                                                  "Received signal {}, exiting.".format(signame)))
    pending = asyncio.Task.all_tasks()
    loop.run_until_complete(asyncio.gather(*pending))


def halt_by_signal(message):
    atexit.unregister(exit_loop)
    exit_loop(message)
    exit()


def exit_loop(message):
    log.info(message)
    pending = asyncio.Task.all_tasks()
    for task in pending:
        # print(task)
        task.cancel()
    asyncio.ensure_future(stop_loop())


async def stop_loop():
    loop.stop()
