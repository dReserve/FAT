"""
The collector collects and stores trade information from exchanges and serves
it to other FATStack processes.
"""

import fatstack as fs
import logging, sys, os.path, json
# import time

collector = sys.modules[__name__]
log = logging.getLogger(__name__)


class TradeBlock:
    """
    One chunk of data retrieved from an exchange server.
    """

    def __init__(self, market, from_trade_id):
        self.market = market
        self.from_trade_id = from_trade_id
        self.from_time = market.exchange.trade_id_to_time(from_trade_id)
        self.cache_file = os.path.join(collector.trade_cache,
                                       self.market.code,
                                       str(self.from_time.year),
                                       str(self.from_time.month),
                                       str(self.from_time.day),
                                       self.from_trade_id)
        self.loaded_from_disk = False

        self.json_block = None
        self.last = None
        self.json_trades = None
        self.trades = None

    async def load_json(self):
        if os.path.isfile(self.cache_file):
            with open(self.cache_file, 'r') as file_handler:
                self.json_block = json.load(file_handler)
            log.info("Found {} in cache.".format(self.cache_file))
            self.loaded_from_disk = True
        else:
            self.json_block = await self.market.exchange.fetch_trade_block(self)
            log.info("Fetched from exchange from {}.".format(self.from_time))

        self.market.exchange.get_trades_from_json(self)

    async def insert_trades(self):
        async with fs.ROOT.Sys.collector.db.pool.acquire() as con:
            records = list(self.trades.itertuples(index=False))
            async with con.transaction():
                await con.copy_records_to_table(self.market.code.lower(), records=records)
                await con.execute(
                        "UPDATE market SET last_stored_trade_id = $1 WHERE code = $2",
                        self.last, self.market.code)
            self.market.last_stored_trade_id = self.last
            self.market.log.info("Inserted %s trades into %s.", len(records), self.market.code)

    async def cache(self):
        if not self.loaded_from_disk:
            if len(self.json_trades) == self.market.exchange.trade_block_len and self.market.not_cached == 0:
                self.dump_json()
                self.market.last_cached_trade_id = self.last
            else:
                self.market.not_cached += len(self.json_trades)
                if self.market.not_cached >= self.market.exchange.trade_block_len:
                    large_trade_block = TradeBlock(self.market, self.market.last_cached_trade_id)
                    large_trade_block.load_json()
                    large_trade_block.dump_json()
                    self.market.last_cached_trade_id = large_trade_block.last
                    self.market.not_cached -= self.len(large_trade_block.json_trades)
            log.info("Saved {} .".format(self.cache_file))

    def dump_json(self):
        if not os.path.isdir(os.path.dirname(self.cache_file)):
            os.makedirs(os.path.dirname(self.cache_file))
        with open(self.cache_file, 'w') as file_handler:
            json.dump(self.json_block, file_handler)

    def __repr__(self):
        return "<TradeBlock market: {}, from_trade_id: {}, from_time: {}>".format(
            self.market.code,
            self.from_trade_id,
            self.from_time)


def init():
    """
    Initializes the Collector.
    """
    log.info("Initializing collector.")
    fs.ROOT.Sys.collector = collector

    collector.trade_cache = os.path.join(fs.ROOT.Config.var_path, fs.ROOT.Config.trade_cache)

    # Setting up the database
    init_query = """CREATE TABLE market (
          code VARCHAR(16) PRIMARY KEY,
          last_stored_trade_id TEXT,
          last_cached_trade_id TEXT,
          not_cached INT)"""

    collector.db = fs.core.Database(fs.ROOT.Config.collector_database, init_query)

    # Start syncing the markets.
    for exchange in fs.ROOT.Config.exchanges:
        exchange.add_common_markets(fs.ROOT.Config.instruments)
        sync_all_markets(exchange)

    log.info("Initialization done.")


def sync_all_markets(exchange):
    """
    Starts tracking the markets on the given exchange.
    """

    exchange.track = True
    for market in exchange.markets:
        log.info("Started syncing {} .".format(market))
        fs.loop.register(sync_market(market))


async def sync_market(market):
    """
    Syncs the given market.
    """
    while True:
        trade_block = TradeBlock(market, market.last_stored_trade_id)
        try:
            await trade_block.load_json()
            await trade_block.insert_trades()
            await trade_block.cache()

        except Exception as e:
            market.log.error(repr(e))
