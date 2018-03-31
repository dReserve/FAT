"""
This module define the exchanges representable in FATStack.
"""


class Instrument:
    "A financial instrument that you can work with in FATStack."

    def start_tracking(self):
        self.track = True

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
