""" The FATStack data server

This process collects and stores trade information from exchanges and serves
it to other FATStack processes.

"""

import fatstack.core
import psycopg2
import asyncio
import signal
import functools
import logging

ROOT = fatstack.core.ROOT

class Collector:
    def __init__(self):
        # Mounting new Collector on ROOT
        ROOT.Collector = self

        # Setting up the database
        self.db = Database()

        # Setting up the event loop
        self.loop = asyncio.get_event_loop()
        for signame in ('SIGINT', 'SIGTERM'):
            self.loop.add_signal_handler(getattr(signal, signame),
                    functools.partial(self.ask_exit, signame))

        # Setting the 'track' flag for Instruments
        for i in ROOT.Config.tracked_instruments:
            i.track = True

        # Setting up tracked Exchanges
        for x in ROOT.Config.tracked_exchanges:
            x.track = True
            markets = x.get_markets(ROOT.Config.tracked_instruments)
            for m in markets:
                logging.info("Tracking: {}".format(m))
                asyncio.ensure_future(m.track())

        logging.info("ROOT: {}".format(ROOT.ls()))

    def ask_exit(self, signame):
        logging.info("\nReceived signal %s, exiting." % signame)
        for task in asyncio.Task.all_tasks():
            task.cancel()
        asyncio.ensure_future(self.exit())

    async def exit(self):
        asyncio.get_event_loop().stop()

    def run_forever(self):
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

class Database:
    """
    This class represents the relational database connection of the Collector.
    """
    def __init__(self):
        self.connection = self.connect_or_init()

    def connect(self):
        return psycopg2.connect(dbname=ROOT.Config.db_name, user=ROOT.Config.db_user,
                                host='localhost', password=ROOT.Config.db_pwd)

    def connect_or_init(self):
        # Connect to an database that's surely exists.
        admin_conn = psycopg2.connect(dbname='postgres', user=ROOT.Config.db_user, host='localhost',
                                    password=ROOT.Config.db_pwd)
        admin_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        admin_cur = admin_conn.cursor()
        admin_cur.execute("SELECT 1 FROM pg_database WHERE datname=%s;",(ROOT.Config.db_name,))

        if not admin_cur.rowcount:
            logging.info("Database doesn't exist, creating one.")
            admin_cur.execute("CREATE DATABASE " + ROOT.Config.db_name)

            conn = self.connect()
            cur = conn.cursor()
            cur.execute("""CREATE TABLE market (id SERIAL PRIMARY KEY,
                                                code VARCHAR(16) UNIQUE,
                                                last INT8);""")

            cur.execute("""CREATE TABLE trade ( price      FLOAT8,
                                                volume     FLOAT8,
                                                time       FLOAT8,
                                                is_buy     BOOL,
                                                is_limit   BOOL,
                                                market     INT4 REFERENCES market ) ;""" )
            conn.commit()
            cur.close()
            logging.info("New database created.")
        else:
            logging.info("Database exists, creating connection.")
            conn = self.connect()

        admin_cur.close()
        admin_conn.close()

        return conn


def start():
    ds = Collector()
    ds.run_forever()
