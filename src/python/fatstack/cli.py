import argparse
from fatstack.core import root

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

    dataserver_parser.add_argument('--dbname', default='postgres')
    dataserver_parser.add_argument('--dbuser', default='postgres')
    dataserver_parser.add_argument('--dbpwd')
    dataserver_parser.add_argument('--dsinstruments', '-I', nargs='*', type=instrument)

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
    print("Command line arguments parsed.")
    args.func(args)

def instrument(i):
    """Converting instrument code to Instrument."""
    try:
        return root.I.__dict__[i.upper()]
    except KeyError:
        msg = "Not a valid instrument: {} .".format(i)
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
