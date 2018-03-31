"""
Building blocks of the FATStack tree.

The command shell starts with a shallow copy of a Tree called ROOT. A user can access every
object which is attached to the ROOT.
"""


class Node:
    "A mount point in the object hierarchy."

    def ls(self):
        "Lists content of the node."
        return list(self.__dict__.keys())


class Tree(Node):
    "The FATStack Tree makes FATStack objects accessable through an object hierarchy."

    def __init__(self):
        from .instruments import Instrument
        from .exchanges import Exchange
        "Creates a tree and loads it up with the defined objects."
        self.bind_codes('Instruments', Instrument)
        self.bind_codes('Exchanges', Exchange)

    def bind_codes(self, name, base_class):
        "Binds objects to the tree by their base class."
        n = Node()
        setattr(self, name, n)
        for C in base_class.__subclasses__():
            o = C()
            setattr(self, C.__name__, o)
            setattr(n, C.__name__, o)
