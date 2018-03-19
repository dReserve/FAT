"""
This module define the exchanges representable in FATStack.
"""
from .tree import Node
import asyncio
import logging
import fatstack.core


class Exchange(Node):
    "An exchange that provides an API for trading."
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
        con = fatstack.core.ROOT.Collector.db.con
        await con.execute("""INSERT INTO market (code, last) VALUES ($1, $2)
                             ON CONFLICT DO NOTHING;""", self.code, 0)
        res = await con.execute("SELECT id, last FROM market WHERE code=$1;", self.code)
        return res

    def __str__(self):
        return "{}".format(self.code)

    def __repr__(self):
        return "<Market exchange: {}, base: {}, quote: {}>".format(self.exchange, self.base,
                                                                   self.quote)

    async def track(self):
        while True:
            self.log.debug("Fetching trades")
            trades = await self.exchange.fetch_trades(self)

            # Sleep if last is closer than update freq


class KRAKEN(Exchange):
    "The Kraken cryptocurrency exchange."
    def __init__(self):
        self.code = self.__class__.__name__

        self.log = logging.getLogger(self.code)

        self.alt_names = {
            'BTC': ('XXBT', 'XBT'),
            'USD': ('ZUSD',),
            'ETH': ('XETH',)}
        self.alt_names_map = {}
        for code, alts in self.alt_names.items():
            for alt in alts:
                self.alt_names_map[alt] = code

        import krakenex    # TO DO: Remove this from here.
        self.api = krakenex.API()
        self.api_call_rate_limit = 6

        loop = asyncio.get_event_loop()
        self.last_api_call = loop.time()

    def get_markets(self, instruments):
        insts = {i.code: i for i in instruments}
        names = {i.code: i.code for i in instruments}
        names.update(self.alt_names_map)

        pairs = self.api.query_public('AssetPairs')['result']

        markets = []
        for pair in pairs:
            for alt, code in names.items():
                if pair.startswith(alt) and code in insts:
                    base = code
                    quote = pair[len(alt):]
                    if quote in names and names[quote] in insts:
                        markets.append(Market(self, insts[base], insts[names[quote]], pair))

        return markets

    async def fetch_trades(self, market):
        loop = asyncio.get_event_loop()
        delta = loop.time() - self.last_api_call

        self.log.debug("Schedueling delta: {:.3f}".format(delta))

        if delta < self.api_call_rate_limit:
            self.last_api_call += self.api_call_rate_limit
            await asyncio.sleep(self.last_api_call - loop.time())
        else:
            self.last_api_call = loop.time()

        # We need to run the krakenex code in executor to maintain asyncron behaviour
        res = await loop.run_in_executor(None, self.api.query_public, 'Trades',
                                         {'pair': market.api_name, 'since': market.last_trade})

        if len(res['error']) == 0:
            trades = res['result'][market.api_name]
            self.log.info("Fetched {} trades from {} .".format(len(trades), market.code))
        else:
            self.log.error(res['error'])

        return trades
