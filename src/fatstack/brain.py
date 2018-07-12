"""
The brain translates trades stored in the collector database into timeframes. A timeframe is similar
to a candle but it stores a bit more data about the trades in thet interval. Notably it stores the
linear regression against the log10 value of price.
"""

import fatstack as fs
import logging, sys
# import time

brain = sys.modules[__name__]
log = logging.getLogger(__name__)


def init():
    log.info("Initializing the brain.")
    fs.ROOT.Sys.brain = brain
