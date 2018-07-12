import fatstack


class DASH(fatstack.core.Instrument):
    "The Dash cryptocurrency."

    def __init__(self):
        self.code = self.__class__.__name__
        self.name = 'Dash'
