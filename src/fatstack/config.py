"""
The config module processes and stores the configuration.

This module acts as a singleton object.
"""

import argparse, importlib, os, logging
import fatstack as fs

# Singleton variables
log = logging.getLogger(__name__)


class ConfigError(Exception):
    """
    Exception raised for errors during the command line parsing.

    Attributes:
        config_var -- name of the problematic config variable
        message -- explanation of the error
    """

    def __init__(self, config_var, message):
        self.config_var = config_var
        self.message = message


def bind():
    cli_parser = create_cli_parser()
    # Parsing arguments
    args = cli_parser.parse_args()
    log.info("Command line arguments parsed.")

    args.config_file = os.path.join(args.etc_path, args.config_file)
    file_conf = parse_config(args.config_file)

    # Merge command line arguments with ones coming from the config file.
    conf_dict = {**args.__dict__, **file_conf}
    # Use cli value if the argument was explicitly set on the commandline.
    for a in cli_parser._actions:
        if a.dest in args:
            value = getattr(args, a.dest)
            if a.default != value:
                conf_dict[a.dest] = value

    conf = argparse.Namespace()
    conf.__dict__ = conf_dict

    # Instantiating instruments and exchanges
    instruments = []
    for i in conf.instruments:
        instruments.append(inst(i))
    exchanges = []
    for x in conf.exchanges:
        exchanges.append(exch(x))
    conf.instruments = instruments
    conf.exchanges = exchanges

    # Preprocessing arguments
    conf.log_dir = os.path.join(conf.var_path, 'log')
    conf.log_file = os.path.join(conf.log_dir, conf.log_file)

    # Mounting the config to the ROOT
    fs.ROOT.Config = conf
    log.info("Configs from {} merged.".format(args.config_file))

    # Setting up var directory
    if not os.path.isdir(conf.var_path):
        log.info("Var directory %s doesn't exists. Creating it.", conf.var_path)
        os.mkdir(conf.var_path)


def create_cli_parser():
    """
    Command line parsing and startup of different modules or the entire stack.
    This will be the processes ROOT tree, the namespace of every shell will be
    a shallow copy of this.
    """
    # The main command line argument parser
    parser = argparse.ArgumentParser(
        description="The dReserve project's Fundamental Algorithmic Trader.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # General arguments
    default_var_path = os.path.realpath(
        os.path.join(os.path.dirname(fs.__file__), "../../var"))
    default_etc_path = os.path.realpath(
        os.path.join(os.path.dirname(fs.__file__), "../../etc"))
    parser.add_argument('-L', '--log-level', default='INFO', help="logging level", metavar='LEVEL')
    parser.add_argument('-l', '--log-file',
                        default="fatstack.log",
                        help="log file name", metavar='FILE')
    parser.add_argument('-c', '--config-file',
                        default="fatstack_config.py",
                        help="config file name", metavar='FILE')
    parser.add_argument('-V', '--var-path',
                        default=default_var_path,
                        help="path to the var directory", metavar='PATH')
    parser.add_argument('-E', '--etc-path',
                        default=default_etc_path,
                        help="path to the etc directory", metavar='PATH')
    parser.add_argument('--version', action='version',
                        version="FATStack {}".format(fs.__version__))

    parser.add_argument(
            '-i', '--instruments', nargs='+', default=[],
            help="Space separated list of instuments to track.")
    parser.add_argument(
            '-x', '--exchanges', nargs='+', default=[],
            help="Space separated list of exchanges to track.")
    parser.add_argument(
            '-t', '--track-interval', type=int, help="Tracking interval in seconds.", default=60)

    # Modules
    parser.add_argument('-C', '--collector', nargs='?', default=False, const=True,
                        help="Collector address.")
    parser.add_argument('-B', '--brain', nargs='?', default=False, const=True,
                        help="Brain address.")
    parser.add_argument('-T', '--trader', nargs='?', default=False, const=True,
                        help="Trader address.")
    parser.add_argument('-S', '--no-shell', default=False, action='store_true',
                        help="Don't run interactive shell.")

    # Collector arguments
    parser.add_argument('-D', '--collector-database', default='postgres@localhost/fatstack',
                        help="The collector's database connection string.")
    parser.add_argument('--trade-cache', default='trade_cache',
                        help="Trade cache directory name.")

    # Database arguments
    parser.add_argument('--admin-database', default='postgres',
                        help="Omnipresent database to connect to during database creation.")

    return parser


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


def parse_config(config_file):
    global_dict, local_dict = {}, {}
    with open(config_file) as config_file_handler:
        exec(config_file_handler.read(), global_dict, local_dict)
    return local_dict
