import fatstack


class ETH(fatstack.core.Instrument):
    "The ether cryptocurrency."

    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'ether'
