""" The FATStack data server

This process collects and stores trade information from exchanges and serves
it to other FATStack processes.

"""

import fatstack.core
import psycopg2
import krakenex
import copy

class DataServer:
    def __init__(self, config):
        # Setting up the server's ROOT Tree
        self.ROOT = copy.copy(fatstack.core.ORIGIN)

        # Making config accessible from the class
        self.ROOT.Config = config

        # Setting up the database

        # Setting the 'track' flag for Instruments
        for i in self.ROOT.Config.tracked_instruments:
            i.track = True

        # Setting up tracked Exchanges
        for x in self.ROOT.Config.tracked_exchanges:
            x.track = True
            markets = x.get_markets(self.ROOT.Config.tracked_instruments)
            print(markets)

        print("ROOT: {}".format(self.ROOT.ls()))

        # print('Adding tracked Pairs.')
        # kraken = self.ROOT.KRAKEN
        #
        # kraken.bind_pairs(args.instruments)
        # print("KRAKEN: {}".format(self.ROOT.Exchanges.KRAKEN.ls()))

        # print('Conencting to the database.')
        # db = psycopg2.connect(dbname=config.db_name, user=config.db_user, host='localhost', password=config.db_pwd)
        #
        # cur = db.cursor()
        #
        # # cur.execute('CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);')
        # # db.commit()
        #
        # cur.close()
        # db.close()

def start(args):
    ds = DataServer(args)
    # ds.loop()
