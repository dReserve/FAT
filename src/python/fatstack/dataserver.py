""" The FATStack data server

This process collects and stores trade information from exchanges and serves
it to other FATStack processes.

"""

import fatstack.core
import psycopg2
import asyncio

class DataServer:
    def __init__(self, ROOT):
        # Mounting ROOT
        self.ROOT = ROOT
        ROOT.DataServer = self

        # Setting up the database
        self.db = Database(ROOT)

        # Setting up the event loop
        self.loop = asyncio.get_event_loop()

        # Setting the 'track' flag for Instruments
        for i in self.ROOT.Config.tracked_instruments:
            i.track = True

        # Setting up tracked Exchanges
        for x in self.ROOT.Config.tracked_exchanges:
            x.track = True
            markets = x.get_markets(self.ROOT.Config.tracked_instruments)
            for m in markets:
                print("Tracking: {}".format(m))
                asyncio.ensure_future(m.track(self.ROOT))

        print("ROOT: {}".format(self.ROOT.ls()))

    def run_forever(self):
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

class Database:
    """
    This class represents the relational database connection of the DataServer.
    """
    def __init__(self, ROOT):
        self.ROOT = ROOT

        self.connection = self.connect_or_init()


    def connect(self):
        return psycopg2.connect(dbname=self.ROOT.Config.db_name, user=self.ROOT.Config.db_user,
                                host='localhost', password=self.ROOT.Config.db_pwd)

    def connect_or_init(self):
        # Connect to an database that's surely exists.
        admin_conn = psycopg2.connect(dbname='postgres', user=self.ROOT.Config.db_user, host='localhost',
                                    password=self.ROOT.Config.db_pwd)
        admin_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        admin_cur = admin_conn.cursor()
        admin_cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;",(self.ROOT.Config.db_name,))

        if not admin_cur.rowcount:
            print("Database doesn't exist, creating one.")
            admin_cur.execute("CREATE DATABASE " + self.ROOT.Config.db_name)

            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""CREATE TABLE market (id SERIAL PRIMARY KEY,
                                                code VARCHAR(16),
                                                last INT8);""")

            cur.execute("""CREATE TABLE trade ( price      FLOAT8,
                                                volume     FLOAT8,
                                                time       FLOAT8,
                                                is_buy     BOOL,
                                                is_limit   BOOL,
                                                market     INT4 REFERENCES market ) ;""" )
            conn.commit()
            cur.close()
            print("New database created.")
        else:
            print("Database exists, creating connection.")
            conn = self.connect()

        admin_cur.close()
        admin_conn.close()

        return conn


def start(args):
    ds = DataServer(args)
    ds.run_forever()
