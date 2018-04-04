import fatstack as fs
import logging
import asyncio
import pandas as pd


class KRAKEN(fs.core.Exchange):
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

        self.last_api_call = fs.loop.loop.time()

    def start_tracking(self, tracked_instruments):
        self.track = True
        markets = self.get_markets(tracked_instruments)
        for market in markets:
            self.log.info("Tracking {}".format(market))
            asyncio.ensure_future(market.track())

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
                        markets.append(fs.core.Market(self, insts[base], insts[names[quote]], pair))

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
        try:
            res = await loop.run_in_executor(
                    None, self.api.query_public, 'Trades',
                    {'pair': market.api_name, 'since': str(market.last_trade)})
        except Exception as e:
            self.log.error(repr(e))
            return None, None

        if len(res['error']) == 0:
            last_id = int(res['result']['last'])
            res = res['result'][market.api_name]
            trades = pd.DataFrame(
                res, columns=['price', 'volume', 'time', 'buy', 'limit', 'misc'])
            del trades['misc']
            trades['price'] = trades['price'].map(lambda x: float(x))
            trades['volume'] = trades['volume'].map(lambda x: float(x))
            trades['buy'] = trades['buy'].map(lambda x: x is 'b')
            trades['limit'] = trades['limit'].map(lambda x: x is 'l')
            trades['market'] = market.db_id
            self.log.info("Fetched {} trades from {} .".format(len(trades), market.code))
            return trades, last_id
        else:
            self.log.error(res['error'])
            return None, None
