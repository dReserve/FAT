import logging, logging.handlers
import time
import os
import argparse
import importlib
import asyncpg

import fatstack as fs


log = logging.getLogger(__name__)
stderr_handler = logging.StreamHandler()
mem_handler = logging.handlers.MemoryHandler(100)
final_log_format = '%(asctime)s %(levelname).1s %(name)s: %(message)s'

# Logging related functions


def bootstrap_logging():
    """
    Runs before command line arguments parsed to setup temporary logger.
    """

    stderr_formatter = logging.Formatter('%(message)s')
    stderr_handler.setFormatter(stderr_formatter)

    logging.root.addHandler(stderr_handler)
    logging.root.addHandler(mem_handler)
    logging.root.setLevel(logging.INFO)


def init_logging(config):
    """
    Sets up final looger now that it knows where to save the log file. Also saves
    events from temporary boot logger set up by bootstrap_logging().
    """

    if not os.path.isdir(config.log_dir):
        log.info("Log dir %s doesn't exists, creating it.", config.log_dir)
        os.mkdir(config.log_dir)

    log.info("Logging into: %s", config.log_file)

    file_handler = logging.FileHandler(config.log_file)
    final_formatter = logging.Formatter(final_log_format)
    file_handler.setFormatter(final_formatter)
    logging.root.addHandler(file_handler)
    mem_handler.setTarget(file_handler)
    mem_handler.flush()
    logging.root.removeHandler(logging.root.handlers[1])

    if config.no_shell:
        stderr_handler.setFormatter(final_formatter)
    else:
        logging.root.removeHandler(stderr_handler)


# Tree objects


class Node:
    "A mount point in the object hierarchy."

    def ls(self):
        "Lists content of the node."
        return list(self.__dict__.keys())


class Tree(Node):
    "The FATStack Tree makes FATStack objects accessable through an object hierarchy."

    def __init__(self):
        "Creates a tree and loads it up with the defined objects."
        self.Instruments = Node()
        self.Exchanges = Node()
        self.Sys = Node()

    def bind_codes(self, name, base_class):
        "Binds objects to the tree by their base class."
        n = Node()
        setattr(self, name, n)
        for C in base_class.__subclasses__():
            o = C()
            setattr(self, C.__name__, o)
            setattr(n, C.__name__, o)


class Instrument:
    "A financial instrument that you can work with in FATStack."

    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Instrument code: {}, name: {}>".format(self.code, self.name)


class Pair:
    """
    A trading pair of two Instruments. An instance of this class attached to an Exchange represents
    a market.
    """

    def __init__(self, base, quote):
        self.base = base
        self.quote = quote
        self.code = base.code + '_' + quote.code

    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Pair base: {}, quote: {}>".format(self.base, self.quote)


class Exchange(Node):
    "An exchange that provides an API for trading."

    def add_common_markets(self, instruments):
        self.markets = self.get_markets(instruments)

    def start_tracking(self):
        self.track = True
        for market in self.markets:
            self.log.info("Tracking {}".format(market))
            fs.loop.register(market.track())

    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Exchange code: {}>".format(self.code)


class Market:
    """
    A tradable market on an Exchange.
    """

    def __init__(self, exchange, base, quote, api_name):
        self.exchange = exchange
        self.base = base
        self.quote = quote
        self.code = str(self.exchange) + '_' + str(self.base) + '_' + str(self.quote)
        self.api_name = api_name

        self.log = logging.getLogger(self.code)

        res = fs.loop.finish(self.init_trade_table())
        self.last_stored_trade_id = res[0]
        self.last_cached_trade_id = res[1]
        self.not_cached = res[2]

    async def init_trade_table(self):
        """
        Initializes trade table for the market.
        """
        db = fs.ROOT.Sys.collector.db

        # Init trade table for market
        if not await db.table_exists(self.code):
            self.log.info("Market table doesn't exist. Creating it.")
            await db.execute("""CREATE TABLE {} ( price      FLOAT8,
                                                  volume     FLOAT8,
                                                  time       TIMESTAMP,
                                                  is_buy     BOOL,
                                                  is_limit   BOOL )""".format(self.code))

        # Init trade cache dir
        self.trade_cache = os.path.join(fs.ROOT.Sys.collector.trade_cache, self.code)
        if not os.path.isdir(self.trade_cache):
            self.log.info("Trade cache dir %s doesn't exists. Creating it.", self.trade_cache)
            os.makedirs(self.trade_cache)

        # The next query only runs if market row doesn't exists yet.
        await db.execute("""INSERT INTO market (code, last_stored_trade_id, last_cached_trade_id, not_cached) VALUES ($1, '0', '0', 0)
                             ON CONFLICT DO NOTHING;""", self.code)
        res = await db.fetchrow("""SELECT last_stored_trade_id, last_cached_trade_id, not_cached
                                     FROM market WHERE code=$1;""", self.code)
        return res

    def __str__(self):
        return "{}".format(self.code)

    def __repr__(self):
        return "<Market exchange: {}, base: {}, quote: {}>".format(self.exchange, self.base,
                                                                   self.quote)

    async def track(self):
        conn = fs.ROOT.Sys.collector.db.conn
        while True:
            self.log.info("Fetching trades since {}".format(
                    time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.last_cached_trade / 1e9))))
            try:
                trade_block = await self.exchange.get_next_trades(self)
                records = list(trade_block.trades.itertuples(index=False))
                async with conn.transaction():
                    await conn.copy_records_to_table(self.code.lower(), records=records)
                    await conn.execute(
                            "UPDATE market SET last = $1 WHERE code = $2",
                            trade_block.last_trade, self.code)
                self.log.info("Inserted %s trades into %s.", len(records), self.code)
                self.last_trade = trade_block.last_trade
            except Exception as e:
                self.log.error(repr(e))


# CLI functions


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
    parser.add_argument('--trade-cache', default='trade_cache',
                        help="Trade cache directory name.")

    # Database arguments
    parser.add_argument('--admin-database', default='postgres',
                        help="Omnipresent database to connect to during database creation.")
    # Parsing arguments
    args = parser.parse_args()

    # Preprocessing arguments
    args.log_dir = os.path.join(args.var_path, 'log')
    args.log_file = os.path.join(args.log_dir, args.log_file)

    # Setting up var directory
    if not os.path.isdir(args.var_path):
        log.info("Var directory %s doesn't exists. Creating it.", args.var_path)
        os.mkdir(args.var_path)

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


# Relational database related functions


class Database:
    """
    This class represents a relational database connection.
    """

    def __init__(self, conn_string, init_query):
        self.server, self.database = conn_string.split('/', 1)
        self.conn_string = conn_string

        fs.loop.finish(self.connect_or_create(init_query))

    async def create_pool(self):
        "Creates a connection pool for the database."
        return await asyncpg.create_pool('postgresql://' + self.conn_string)

    async def connect_or_create(self, init_query):
        "Connects to exiting database or creates it."
        # Connect to an 'admin' database that's surely exists.
        admin_conn = await asyncpg.connect(
                'postgresql://' + self.server + '/' + fs.ROOT.Config.admin_database)

        res = await admin_conn.fetch(
            "SELECT 1 FROM pg_database WHERE datname=$1", self.database)

        if not res:
            log.info("Database doesn't exist, creating one.")
            await admin_conn.execute("CREATE DATABASE {}".format(self.database))

            self.pool = await self.create_pool()
            async with self.pool.acquire() as con:
                await con.execute(init_query)

            log.info("New database and connection pool created.")
        else:
            log.info("Database exists, creating connection pool.")
            self.pool = await self.create_pool()

        await admin_conn.close()

    async def execute(self, query, *args):
        "Executes the query with the given arguments."
        async with self.pool.acquire() as con:
            return await con.execute(query, *args)

    async def fetchrow(self, query, *args):
        "Fetches one row with the given arguments."
        async with self.pool.acquire() as con:
            return await con.fetchrow(query, *args)

    async def table_exists(self, table):
        "Returns True if the table exists in the represented database."
        relation_name = 'public.' + table
        async with self.pool.acquire() as con:
            res = await con.fetchrow("SELECT to_regclass($1)", relation_name)
        return bool(res['to_regclass'])
