import logging, logging.handlers
import os, asyncpg

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

    def get_markets(self, instruments):
        """
        Retrieve the supported markets from the exchange. Implemented in the child classes.
        """

    async def add_common_markets(self, instruments):
        self.markets = await self.get_markets(instruments)

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

    async def sync_db(self):
        res = await self.init_trade_table()
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


# CLI functions


# Relational database related functions


class Database:
    """
    This class represents a relational database connection.
    """

    def __init__(self, conn_string, init_query):
        self.server, self.database = conn_string.split('/', 1)
        self.conn_string = conn_string
        self.init_query = init_query

    async def create_pool(self):
        "Creates a connection pool for the database."
        return await asyncpg.create_pool('postgresql://' + self.conn_string)

    async def connect_or_create(self):
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
