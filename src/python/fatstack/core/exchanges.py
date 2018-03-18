"""
This module define the exchanges representable in FATStack.
"""
from .tree import Node
import asyncio
import logging
import fatstack.core

# Base classes
class Exchange(Node):
    "An exchange that provides a API for trading."
    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Exchange code: {}>".format(self.code)

class Market:
    "A tradable instument Pair on an Exchange."
    def __init__(self, exchange, base, quote, api_name):
        ROOT = fatstack.core.ROOT
        self.exchange = exchange
        self.base = base
        self.quote = quote
        self.code = str(self.exchange) + '_' + str(self.base) + '_' + str(self.quote)
        self.api_name = api_name

        cursor = ROOT.Collector.db.connection.cursor()
        cursor.execute("""INSERT INTO market (code, last) VALUES (%s, %s)
                            ON CONFLICT DO NOTHING;""", (self.code, 0))
        cursor.execute("SELECT id, last FROM market WHERE code=%s;", (self.code,))
        result = cursor.fetchone()
        self.db_id = result[0]
        self.last_trade = result[1]
        ROOT.Collector.db.connection.commit()
        cursor.close()

    def __str__(self):
        return "{}".format(self.code)

    def __repr__(self):
        return "<Market exchange: {}, base: {}, quote: {}, api_name: {}>".format(self.exchange, self.base,
                self.quote, self.api_name)

    async def track(self):
        ROOT = fatstack.core.ROOT

        while True:
            self.exchange.collect_trades(self)
            await asyncio.sleep(ROOT.Config.timeout)
        return False


# Exchanges
class KRAKEN(Exchange):
    "The Kraken cryptocurrency exchange."
    def __init__(self):
        self.code = self.__class__.__name__

        self.log = logging.getLogger(self.code)

        self.alt_names = {
            'BTC': ('XXBT', 'XBT'),
            'USD': ('ZUSD',),
            'ETH': ('XETH',) }
        self.alt_names_map = {}
        for code, alts in self.alt_names.items():
            for alt in alts:
                self.alt_names_map[alt] = code

        import krakenex    # TO DO: Remove this from here.
        self.api = krakenex.API()
        self.last_api_call = 0
        self.track = False

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

    def collect_trades(self, market):
        loop = asyncio.get_event_loop()
        start = loop.time()
        delta = start - self.last_api_call
        self.log.debug("Schedueling delta: {:.3f}".format(delta))
        if delta < 2:
            start = self.last_api_call + 2
        self.last_api_call = start
        loop.call_at(start, self._do_collect_trades, market)
        self.log.debug("Scheduling API call at {} for {} .".format(self.last_api_call, market.code))

    def _do_collect_trades(self, market):
        loop = asyncio.get_event_loop()
        self.log.debug("API call at {} for {} .".format(loop.time(), market.code))
        raw_trades = self.api.query_public('Trades',
                                      {'pair':market.api_name, 'since':market.last_trade})
        if len(raw_trades['error']) == 0:
            trades = raw_trades['result'][market.api_name]
            self.log.info("Collected {} trades from {} .".format(len(trades), market.code))
        else:
            self.log.error(raw_trades['error'])

    async def api_scheduler(self, timeout):
        while True:
            await asyncio.sleep(timeout)
            self.log.info("Inside {}s scheduler.".format(self.code))
        return False
