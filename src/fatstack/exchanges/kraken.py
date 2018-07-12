import fatstack as fs
import logging, asyncio, datetime, math
import pandas as pd
import krakenex    # TO DO: Remove this from here.


class KRAKENApiError(Exception):
    pass


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

        self.api = krakenex.API()
        self.api_call_rate_limit = 6
        self.trade_block_len = 1000

        self.last_api_call = asyncio.get_event_loop().time()

    async def get_markets(self, instruments):
        """
        Creates markets specified by the instrument list. It creates a market object for every
        existing matket on the exchange which has both the base and the quote in the instruments
        list.
        """
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
                        market = fs.core.Market(self, insts[base], insts[names[quote]], pair)
                        await market.sync_db()
                        markets.append(market)

        return markets

    def trade_id_to_time(self, trade_id):
        return datetime.datetime.utcfromtimestamp(int(trade_id) / 1e9)

    async def fetch_trade_block(self, trade_block):
        """
        Fetches the trades from the exchange naively taking care of API overloading.
        """

        loop = asyncio.get_event_loop()
        delta = loop.time() - self.last_api_call

        self.log.debug("Schedueling delta: {:.3f}".format(delta))

        if delta < self.api_call_rate_limit:
            self.last_api_call += self.api_call_rate_limit
            await asyncio.sleep(self.last_api_call - loop.time())
        else:
            self.last_api_call = loop.time()

        # We need to run the krakenex code in executor to maintain asyncron behaviour
        json_block = await loop.run_in_executor(
                None, self.api.query_public, 'Trades',
                {'pair': trade_block.market.api_name, 'since': str(trade_block.from_trade_id)})

        if len(json_block['error']) != 0:
            raise KRAKENApiError(self.json_block['error'])

        return json_block

    def get_trades_from_json(self, trade_block):
        trade_block.last = trade_block.json_block['result']['last']
        trade_block.json_trades = trade_block.json_block['result'][trade_block.market.api_name]

        trades = pd.DataFrame(
            trade_block.json_trades, columns=['price', 'volume', 'time', 'buy', 'limit', 'misc'])
        del trades['misc']
        trades['price'] = trades['price'].map(lambda x: math.log10(float(x)))
        trades['volume'] = trades['volume'].map(lambda x: float(x))
        trades['time'] = trades['time'].map(lambda x: datetime.datetime.utcfromtimestamp(x))
        trades['buy'] = trades['buy'].map(lambda x: x is 'b')
        trades['limit'] = trades['limit'].map(lambda x: x is 'l')

        trade_block.trades = trades
