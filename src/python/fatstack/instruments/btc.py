import fatstack


class BTC(fatstack.core.Instrument):
    "The bitcoin cryptocurrency. See https://bitcoin.org for more."

    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'bitcoin'
