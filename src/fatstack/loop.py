import fatstack as fs
import asyncio
import logging
import atexit
import signal
import functools
import sys


loop = sys.modules[__name__]
log = logging.getLogger(__name__)
event_loop = asyncio.get_event_loop()


def init():
    fs.ROOT.Sys.loop = loop
    atexit.register(exit_loop, 'Exiting.')
    for signame in ('SIGINT', 'SIGTERM'):
        add_signal_handler(getattr(signal, signame),
                           functools.partial(halt_by_signal,
                                             "Received signal {}, exiting.".format(signame)))


def register(task):
    asyncio.ensure_future(task)


def finish(task):
    return event_loop.run_until_complete(task)


def finish_all():
    """ Finish all registered tasks. """
    pending = asyncio.Task.all_tasks()
    loop.finish(asyncio.gather(*pending))


def time():
    return event_loop.time()


def add_signal_handler(signum, callback, *args):
    event_loop.add_signal_handler(signum, callback, *args)


def remove_signal_handler(signum):
    event_loop.remove_signal_handler(signum)


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
    event_loop.stop()
