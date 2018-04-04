"""

Core classes used by all FATStack processes

"""
from .tree import *
from .instruments import *
from .exchanges import *
import fatstack.core.loop

ROOT = Tree()
