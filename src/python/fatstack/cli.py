import argparse
import logging

import fatstack.core
ROOT = fatstack.core.ROOT


class ConfigError(Exception):
    """Exception raised for errors in the config.

    Attributes:
        config_var -- name of the problematic config variable
        message -- explanation of the error
    """

    def __init__(self, config_var, message):
        self.config_var = config_var
        self.message = message


def startup():
    """
    Command line parsing and startup of different modules or the entire stack.
    This will be the processes ROOT tree, the namespace of every shell will be
    a shallow copy of this.
    """

    # The main command line argument parser
    parser = argparse.ArgumentParser(description="The dReserve project's Fundamental Algorithmic Trader.")
    subparsers = parser.add_subparsers()

    # The default command is the shell.
    parser.set_defaults(func=shell)
    parser.add_argument('-L', '--log-level', default='INFO', help="logging level", metavar='LEVEL')

    # The shell parser
    shell_parser = subparsers.add_parser(
            name="shell",
            aliases=['sh'],
            description="Allows to give commands to traders.",
            help="Starts a trader process.")

    shell_parser.set_defaults(func=shell)

    # The collector parser
    collector_parser = subparsers.add_parser(
            name="collector",
            aliases=['co'],
            description="Collects and stores trade data from exchanges and serves this to simulators.",
            help="Starts a collector process.")

    collector_parser.add_argument('--db-name', default='fatstack')
    collector_parser.add_argument('--db-user', default='postgres')
    collector_parser.add_argument('--db-pwd')
    collector_parser.add_argument(
            '--instruments', '-i', nargs='+', dest='tracked_instruments', type=inst,
            help="Space separated list of supported instuments to track.", default=[])
    collector_parser.add_argument(
            '--exchanges', '-x', nargs='+', dest='tracked_exchanges', type=exch,
            help="Space separated list of supported exchanges to track.", default=[])
    collector_parser.add_argument(
            '--timeout', '-t', type=int, help="Tracking timeout.", default=2)

    collector_parser.set_defaults(func=collector)

    # The brain parser
    simulator_parser = subparsers.add_parser(
            name="brain",
            aliases=['br'],
            description="Processes trade data into timeframes and allows analysis on these.",
            help="Starts a brain process.")

    simulator_parser.set_defaults(func=brain)

    # The trader parser.
    trader_parser = subparsers.add_parser(
            name="trader",
            aliases=['tr'],
            description=("Connects to exchanges and blockchain accounts and manages trades and"
                         "balances on them."),
            help="Starts a trader process.")

    trader_parser.set_defaults(func=trader)

    # Parsing arguments
    args = parser.parse_args()

    # Setting up logging
    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format='%(asctime)s %(levelname).1s %(name)s: %(message)s')
    log = logging.getLogger("Cli")

    if len(args.tracked_instruments) < 2:
        raise ConfigError('tracked_instruments', "Collector needs at least two instrument.")
    if len(args.tracked_exchanges) < 1:
        raise ConfigError('tracked_exchanges', "Collector needs at least one exchange to track.")
    log.info("Command line arguments parsed.")

    # Mounting the config to the ROOT
    ROOT.Config = args

    # Calling the function selected by the subcommand
    args.func(args)


# Special type converters for FATS specific command line arguments.
def inst(i):
    """
    Converting an instrument code to an Instrument object. Also does type checking at the same
    time.
    """
    try:
        return getattr(ROOT.Instruments, i.upper())
    except KeyError:
        msg = "Not a valid instrument: {} .".format(i)
        raise argparse.ArgumentTypeError(msg)

def exch(x):
    """
    Converting an exchange code to an Exchange object. Also does type checking at the same
    time.
    """
    try:
        return getattr(ROOT.Exchanges, x.upper())
    except KeyError:
        msg = "Not a valid exchange: {} .".format(x)
        raise argparse.ArgumentTypeError(msg)


# Functions of the different subcommands.
def shell(config):
    logging.info("Running the Shell.")


def collector(config):
    """ Starting the Collector. """
    import fatstack.collector
    fatstack.collector.start()


def brain(config):
    logging.info("Running the Brain.")


def trader(config):
    logging.info("Running the Trader.")
