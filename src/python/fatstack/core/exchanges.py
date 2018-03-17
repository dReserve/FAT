"""
This module define the exchanges representable in FATStack.
"""
from .tree import *
import asyncio
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
        self.exchange = exchange
        self.base = base
        self.quote = quote
        self.api_name = api_name

    def __str__(self):
        return "{}_{}_{}".format(self.base, self.quote, self.exchange)

    def __repr__(self):
        return "<Market exchange: {}, base: {}, quote: {}, api_name: {}>".format(self.exchange, self.base,
                self.quote, self.api_name)

    async def track(self):
        ROOT = fatstack.core.ROOT
        while True:
            print("Inside {}s tracker @{} .".format(self, ROOT.Collector.loop.time()))
            await asyncio.sleep(ROOT.Config.timeout)
        return False


# Exchanges
class KRAKEN(Exchange):
    "The Kraken cryptocurrency exchange."
    def __init__(self):
        self.code = self.__class__.__name__

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


    async def api_scheduler(self, timeout):
        while True:
            await asyncio.sleep(timeout)
            print("Inside {}s scheduler.".format(self.code))
        return False
