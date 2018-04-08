import asyncio
import logging
import time
import fatstack as fs


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

    def start_tracking(self, instruments):
        self.track = True
        for market in self.get_markets(instruments):
            self.log.info("Tracking {}".format(market))
            fs.loop.register(market.track())

    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Exchange code: {}>".format(self.code)


class Market:
    "A tradable instument Pair on an Exchange."

    def __init__(self, exchange, base, quote, api_name):
        self.exchange = exchange
        self.base = base
        self.quote = quote
        self.code = str(self.exchange) + '_' + str(self.base) + '_' + str(self.quote)
        self.api_name = api_name

        self.log = logging.getLogger(self.code)

        res = asyncio.get_event_loop().run_until_complete(self.init_market_table())
        self.db_id = res[0]
        self.last_trade = res[1]

    async def init_market_table(self):
        conn = fs.ROOT.Sys.collector.db.conn
        await conn.execute("""INSERT INTO market (code, last) VALUES ($1, $2)
                             ON CONFLICT DO NOTHING;""", self.code, 0)
        res = await conn.fetchrow("SELECT id, last FROM market WHERE code=$1;", self.code)
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
                    time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.last_trade / 1e9))))
            trades, last_trade = await self.exchange.fetch_trades(self)
            if trades is not None:
                records = list(trades.itertuples(index=False))
                async with conn.transaction():
                    await conn.copy_records_to_table('trade', records=records)
                    await conn.execute(
                            "UPDATE market SET last = $1 WHERE id = $2",
                            last_trade, self.db_id)
                self.last_trade = last_trade
