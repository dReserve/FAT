import argparse, os, logging, importlib
import fatstack as fs

log = logging.getLogger(__name__)


class ConfigError(Exception):
    """Exception raised for errors in the config.

    Attributes:
        config_var -- name of the problematic config variable
        message -- explanation of the error
    """

    def __init__(self, config_var, message):
        self.config_var = config_var
        self.message = message


def parse_args():
    """
    Command line parsing and startup of different modules or the entire stack.
    This will be the processes ROOT tree, the namespace of every shell will be
    a shallow copy of this.
    """
    # The main command line argument parser
    parser = argparse.ArgumentParser(
        description="The dReserve project's Fundamental Algorithmic Trader.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # The default command is the shell.
    parser.set_defaults(func=shell)

    # General arguments
    default_var_path = os.path.realpath(
        os.path.join(os.path.dirname(fs.__file__), "../../../var"))
    parser.add_argument('-L', '--log-level', default='INFO', help="logging level", metavar='LEVEL')
    parser.add_argument('-l', '--log-file',
                        default="fatstack.log",
                        help="log file name", metavar='FILE')
    parser.add_argument('-V', '--var-path',
                        default=default_var_path,
                        help="path to the var directory", metavar='PATH')
    parser.add_argument('--version', action='version',
                        version="FATStack {}".format(fs.__version__))

    parser.add_argument(
            '-i', '--instruments', nargs='+', type=inst, default=[],
            help="Space separated list of instuments to track.")
    parser.add_argument(
            '-x', '--exchanges', nargs='+', type=exch, default=[],
            help="Space separated list of exchanges to track.")
    parser.add_argument(
            '-t', '--track-interval', type=int, help="Tracking interval in seconds.", default=60)

    # Modules
    parser.add_argument('-C', '--collector', nargs='?', default=False, const=True,
                        help="Collector address.")
    parser.add_argument('-B', '--brain', default='',
                        help="Brain address.")
    parser.add_argument('-T', '--trader', default='',
                        help="Trader address.")
    parser.add_argument('-S', '--no-shell', default=False, action='store_true',
                        help="Don't run interactive shell.")

    # Collector arguments
    parser.add_argument('-D', '--collector-database', default='postgres@localhost/fatstack',
                        help="The collector's database connection string.")

    # Database arguments
    parser.add_argument('--admin-database', default='postgres',
                        help="Omnipresent database to connect to during database creation.")
    # Parsing arguments
    args = parser.parse_args()

    # Setting up var directory
    if os.path.isdir(args.var_path):
        print("Var exists.", args.var_path)
    else:
        print("Var doesn't exists.", args.var_path)
        os.mkdir(args.var_path)

    # if len(args.instruments) < 2:
    #     log.error("Not enough instruments specified.")
    #     raise ConfigError('tracked_instruments', "FATStack needs at least two instrument.")
    # if len(args.exchanges) < 1:
    #     log.error("No exchange specified.")
    #     raise ConfigError('tracked_exchanges', "FATStack needs at least one exchange to track.")
    # log.info("Command line arguments parsed.")

    # Mounting the config to the ROOT
    fs.ROOT.Config = args
    log.info("Command line arguments parsed.")


# Special type converters for FATS specific command line arguments.
def inst(i):
    """
    Converting an instrument code to an Instrument object. Also does type checking at the same
    time.
    """
    try:
        instrument_module = importlib.import_module('fatstack.instruments.{}'.format(i.lower()))
        instrument_class = getattr(instrument_module, i.upper())
        instrument = instrument_class()
        setattr(fs.ROOT, i.upper(), instrument)
        setattr(fs.ROOT.Instruments, i.upper(), instrument)
        return instrument
    except ModuleNotFoundError:
        msg = "Not a valid instrument: {} .".format(i)
        raise argparse.ArgumentTypeError(msg)


def exch(x):
    """
    Converting an exchange code to an Exchange object. Also does type checking at the same
    time.
    """
    try:
        exchange_module = importlib.import_module('fatstack.exchanges.{}'.format(x.lower()))
        exchange_class = getattr(exchange_module, x.upper())
        exchange = exchange_class()
        setattr(fs.ROOT, x.upper(), exchange)
        setattr(fs.ROOT.Exchanges, x.upper(), exchange)
        return exchange
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
