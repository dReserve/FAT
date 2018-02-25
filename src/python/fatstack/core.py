"""

Core classes used by all processes

"""

class Node:
    pass

class Tree:
    def __init__(self):
        # Binding Instruments
        self.bind_codes('I', Instrument)
        self.bind_codes('X', Exchange)

    def bind_codes(self, name, base_class):
        n = self.__dict__[name] = Node()
        for C in base_class.__subclasses__():
            o = self.__dict__[C.__name__] = C()
            n.__dict__[C.__name__] = o

class Instrument:
    def __str__(self):
        return self.code

    def __repr__(self):
        return "<Instrument code: {}, name: {}>".format(self.code, self.name)

class Pair:
    def __init__(self, base, quote):
        self.base = base
        self.quote = quote

    def __str__(self):
        return "{}{}".format(self.base.__str__(), self.quote.__str__())

    def __repr__(self):
        return "<Pair base: {}, quote: {}>".format(self.base.code, self.quote.code)

class Exchange:
    def __repr__(self):
        return "<Exchange code: {}>".format(self.code)

# Instruments
class BTC(Instrument):
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'bitcoin'

class ETH(Instrument):
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'ether'

class USD(Instrument):
    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'dollar'

# Exchanges
class KRAKEN(Exchange):
    def __init__(self):
        self.code = self.__class__.__name__
        self.name_map = {
            'BTC': ('XXBT', 'XBT'),
            'USD': ('ZUSD',),
            'ETH': ('XETH',) }

root = Tree()
