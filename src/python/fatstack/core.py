"""

Core classes used by all FATStack processes

"""

class Node:
    "A mount point in the object hierarchy."
    def ls(self):
        "Lists content of the node."
        return list(self.__dict__.keys())

class Tree(Node):
    "The FATStack Tree makes FATStack objects accessable through an object hierarchy."
    def __init__(self):
        "Creates a tree and loads it up with the defined objects."
        self.bind_codes('Instruments', Instrument)
        self.bind_codes('Exchanges', Exchange)

    def bind_codes(self, name, base_class):
        "Binds objects to the tree by their base class."
        n = Node()
        setattr(self, name, n)
        for C in base_class.__subclasses__():
            o = C()
            setattr(self,C.__name__, o)
            setattr(n, C.__name__, o)

class Instrument:
    "A financial instrument that you can work with in FATStack."
    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Instrument code: {}, name: {}>".format(self.code, self.name)

class Pair:
    "A trading pair of two Instruments. An instance of this class attached to an Exchange represents a market."
    def __init__(self, base, quote):
        self.base = base
        self.quote = quote
        self.code = base.code + '_' + quote.code

    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Pair base: {}, quote: {}>".format(self.base, self.quote)

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
        return "<Market exchange: {}, base: {}, quote: {}>".format(self.exchange, self.base, self.quote)

# Instruments
class BTC(Instrument):
    "The bitcoin cryptocurrency. See https://bitcoin.org for more."
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'bitcoin'

class ETH(Instrument):
    "The ether cryptocurrency."
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'ether'

class USD(Instrument):
    "USA dollar."
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'dollar'

class DASH(Instrument):
    "The Dash cryptocurrency."
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'Dash'


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
