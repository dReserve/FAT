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
        self.bind_codes('I', Instrument)
        self.bind_codes('X', Exchange)

    def bind_codes(self, name, base_class):
        "Binds objects to the tree by their base class."
        n = self.__dict__[name] = Node()
        for C in base_class.__subclasses__():
            o = self.__dict__[C.__name__] = C()
            n.__dict__[C.__name__] = o

class Instrument:
    "A financial instrument that you can work with in FATStack."
    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Instrument code: {}, name: {}>".format(self.code, self.name)

class Pair:
    "A trading pair of two Instruments. An instance of this class attached to an Exchange represents a market."
    def __init__(self, base, quote, api_name):
        self.base = base
        self.quote = quote
        self.api_name = api_name

    def __str__(self):
        return "{}{}".format(self.base.__str__(), self.quote.__str__())

    def __repr__(self):
        return "<Pair base: {}, quote: {}>".format(self.base.code, self.quote.code)

class Exchange(Node):
    "An exchange that provides a API for trading."
    def __repr__(self):
        return "<Exchange code: {}>".format(self.code)

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
        self.name_map = {
            'BTC': ('XXBT', 'XBT'),
            'USD': ('ZUSD',),
            'ETH': ('XETH',) }
        import krakenex
        self.api = krakenex.API()

    def names(self):
        ns = {k: k for k, v in dict.fromkeys(root.I.ls()).items()}
        print(ns)
        for name, alts in self.name_map.items():
            if alts:
                for alt in alts:
                    ns[alt] = name
        return ns

    def bind_pairs(self, instruments):
        insts = [i.code for i in instruments]
        names = self.names()
        pairs = self.api.query_public('AssetPairs')['result']
        for pair in pairs:
            for alt, code in names.items():
                if pair.startswith(alt) and code in insts:
                    base = root.I.__dict__[code]
                    quote = pair[len(alt):]
                    if quote in names and names[quote] in insts:
                        quote = root.I.__dict__[names[quote]]
                        c = base.code + '_' + quote.code
                        p = root.__dict__[c] = Pair(base, quote, pair)
                        root.X.KRAKEN.__dict__[c] = p


root = Tree()
