import argparse
from fatstack.core import ORIGIN

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
    # Command line parsing and startup of different modules or the entire stack.

    # The main parser.
    parser = argparse.ArgumentParser(description="The dReserve project's Fundamental Algorithmic Trader.")
    parser.set_defaults(func=shell)
    subparsers = parser.add_subparsers()

    # The shell parser
    shell_parser = subparsers.add_parser(
            name = "shell",
            aliases=['cli'],
            description = "Allows to give commands to traders.",
            help = "Starts a trader process." )

    shell_parser.set_defaults(func=shell)

    # The dataserver parser.
    dataserver_parser = subparsers.add_parser(
            name = "dataserver",
            aliases=['ds'],
            description = "Collects and stores trade data from exchanges and serves this to simulators.",
            help = "Starts a dataserver process." )

    dataserver_parser.add_argument('--db-name', default='fatstack')
    dataserver_parser.add_argument('--db-user', default='postgres')
    dataserver_parser.add_argument('--db-pwd')
    dataserver_parser.add_argument('--instruments', '-i', nargs='+', dest='tracked_instruments',
            type=instrument, help="Space separated list of supported instuments to track.", default=[])
    dataserver_parser.add_argument('--exchanges', '-x', nargs='+', dest='tracked_exchanges',
            type=exchange, help="Space separated list of supported exchanges to track.", default=[])

    dataserver_parser.set_defaults(func=dataserver)

    # The simulator parser.
    simulator_parser = subparsers.add_parser(
            name = "simulator",
            aliases=['sim'],
            description = "Processes trade data into timeframes and allows analysis on these.",
            help = "Starts a simulator process." )

    simulator_parser.set_defaults(func=simulator)

    # The trader parser.
    trader_parser = subparsers.add_parser(
            name = "trader",
            aliases=['trd'],
            description = ( "Connects to exchanges and blockchain accounts and manages trades and"
                            "balances on them." ),
            help = "Starts a trader process." )

    trader_parser.set_defaults(func=trader)

    args = parser.parse_args()
    if len(args.tracked_instruments) < 2: raise ConfigError('tracked_instruments', "DS needs at least two instrument.")
    if len(args.tracked_exchanges) < 1: raise ConfigError('tracked_exchanges', "DS needs at least one exchange to track.")
    print("Command line arguments parsed.")
    args.func(args)

def instrument(i):
    """
    Converting an instrument code to an Instrument object. Also does type checking at the same
    time.
    """
    try:
        return getattr(ORIGIN.Instruments, i.upper())
    except KeyError:
        msg = "Not a valid instrument: {} .".format(i)
        raise argparse.ArgumentTypeError(msg)

def exchange(x):
    """
    Converting an exchange code to an Exchange object. Also does type checking at the same
    time.
    """
    try:
        return getattr(ORIGIN.Exchanges, x.upper())
    except KeyError:
        msg = "Not a valid exchange: {} .".format(x)
        raise argparse.ArgumentTypeError(msg)

def shell(args):
    print("Running the CLI shell.")

def dataserver(args):
    import fatstack.dataserver
    fatstack.dataserver.start(args)

def simulator(args):
    print("Running the simulator.")

def trader(args):
    print("Running the trader.")
