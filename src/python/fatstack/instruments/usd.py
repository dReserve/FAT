import fatstack


class USD(fatstack.core.Instrument):
    "USA dollar."

    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'dollar'
