import argparse
import fatstack.core

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

    # The fatstack ROOT tree is created here. It will be passed to the process object.
    ROOT = fatstack.core.Tree()


    # Functions of the different subcommands. They are here to see ROOT.
    def shell(config):
        print("Running the CLI shell.")

    def dataserver(config):
        """ Starting the dataserver. """
        import fatstack.dataserver
        fatstack.dataserver.start(ROOT)

    def simulator(config):
        print("Running the simulator.")

    def trader(config):
        print("Running the trader.")


    # Type checkers and converters for different FATStack objects. They are here to see ROOT.
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


    # The main command line argument parser
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

    # The dataserver parser
    dataserver_parser = subparsers.add_parser(
            name = "dataserver",
            aliases=['ds'],
            description = "Collects and stores trade data from exchanges and serves this to simulators.",
            help = "Starts a dataserver process." )

    dataserver_parser.add_argument('--db-name', default='fatstack')
    dataserver_parser.add_argument('--db-user', default='postgres')
    dataserver_parser.add_argument('--db-pwd')
    dataserver_parser.add_argument('--instruments', '-i', nargs='+', dest='tracked_instruments',
            type=inst, help="Space separated list of supported instuments to track.", default=[])
    dataserver_parser.add_argument('--exchanges', '-x', nargs='+', dest='tracked_exchanges',
            type=exch, help="Space separated list of supported exchanges to track.", default=[])
    dataserver_parser.add_argument('--timeout', '-t', type=int, help="Tracking timeout.", default=2)

    dataserver_parser.set_defaults(func=dataserver)

    # The simulator parser
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

    # Mounting the config to the ROOT
    ROOT.Config = args

    # Calling the function selected by the subcommand
    args.func(args)
