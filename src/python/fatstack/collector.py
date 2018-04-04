""" The FATStack data server

This process collects and stores trade information from exchanges and serves
it to other FATStack processes.

"""

import fatstack as fs
import asyncpg
import asyncio
import logging
import fatstack.shell


class Collector:
    def __init__(self):
        fs.ROOT.Sys.Collector = self
        # Setting up the database
        self.db = Database()

        self.log = logging.getLogger("Collector")

        # Start instrument tracking
        for instrument in fs.ROOT.Config.tracked_instruments:
            instrument.start_tracking()

        # Start exchange tracking
        for exchange in fs.ROOT.Config.tracked_exchanges:
            exchange.start_tracking(fs.ROOT.Config.tracked_instruments)

        self.log.debug("ROOT: {}".format(fs.ROOT.ls()))


class Database:
    """
    This class represents the relational database connection of the Collector.
    """

    def __init__(self):
        self.log = logging.getLogger("Database")
        self.con = asyncio.get_event_loop().run_until_complete(self.connect_or_init())

    async def connect(self):
        return await asyncpg.connect(
            database=fs.ROOT.Config.db_name,
            user=fs.ROOT.Config.db_user,
            host='localhost',
            password=fs.ROOT.Config.db_pwd)

    async def connect_or_init(self):
        # Connect to an database that's surely exists.
        admin_con = await asyncpg.connect(
            database='postgres',
            user=fs.ROOT.Config.db_user,
            host='localhost',
            password=fs.ROOT.Config.db_pwd)

        res = await admin_con.fetch(
            "SELECT 1 FROM pg_database WHERE datname=$1", fs.ROOT.Config.db_name)

        if not res:
            self.log.info("Database doesn't exist, creating one.")
            await admin_con.execute("CREATE DATABASE {}".format(fs.ROOT.Config.db_name))

            con = await self.connect()

            async with con.transaction():
                await con.execute("""CREATE TABLE market (id SERIAL PRIMARY KEY,
                                                    code VARCHAR(16) UNIQUE,
                                                    last INT8)""")

                await con.execute("""CREATE TABLE trade ( price      FLOAT8,
                                                    volume     FLOAT8,
                                                    time       FLOAT8,
                                                    is_buy     BOOL,
                                                    is_limit   BOOL,
                                                    market     INT4 REFERENCES market )""")

            self.log.info("New database created.")
        else:
            self.log.info("Database exists, creating connection.")
            con = await self.connect()

        await admin_con.close()
        return con


def start():
    fs.ROOT.Sys.loop = asyncio.get_event_loop()
    Collector()
    fs.ROOT.Sys.shell = fatstack.shell.Shell(fs.ROOT.__dict__)
    fatstack.loop.run_loop()
