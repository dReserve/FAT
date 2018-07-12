import fatstack.core as core
import fatstack.config as config
import logging

__version__ = '0.0.0'


def start():
    core.bootstrap_logging()
    log = logging.getLogger(__file__)

    log.info("Starting FATStack %s.", __version__)
    config.bind()

    core.init_logging(ROOT.Config)

    # Initializing the event loop
    # loop.init()

    if ROOT.Config.collector:
        import fatstack.collector
        fatstack.collector.bind()

    if ROOT.Config.brain:
        import fatstack.brain
        fatstack.brain.init()

    # if not ROOT.Config.no_shell:
    #     import fatstack.shell
    #     ROOT.Sys.shell = fatstack.shell.Shell(ROOT.__dict__)
    #     log.info("Initialization finished, entering the shell.")


# This is the root of the fatstack tree. We mount user accessible objects under this object.
ROOT = core.Tree()
