import fatstack as fs
import asyncpg
import logging

log = logging.getLogger("Database")


class Database:
    """
    This class represents a relational database connection.
    """

    def __init__(self, conn_string):
        self.server, self.database = conn_string.split('/', 1)
        self.conn_string = conn_string

        fs.loop.finish(self.connect_or_create())

    async def connect(self):
        return await asyncpg.connect('postgresql://' + self.conn_string)

    async def connect_or_create(self):
        admin_conn_string = 'postgresql://' + self.server + '/' + fs.ROOT.Config.admin_database
        # Connect to an database that's surely exists.
        admin_conn = await asyncpg.connect(admin_conn_string)

        res = await admin_conn.fetch(
            "SELECT 1 FROM pg_database WHERE datname=$1", self.database)

        if not res:
            log.info("Database doesn't exist, creating one.")
            await admin_conn.execute("CREATE DATABASE {}".format(self.database))

            self.conn = await self.connect()

            await self.execute("""CREATE TABLE market (id SERIAL PRIMARY KEY,
                                  code VARCHAR(16) UNIQUE,
                                  last INT8)""")

            await self.conn.execute("""CREATE TABLE trade ( price      FLOAT8,
                                                volume     FLOAT8,
                                                time       FLOAT8,
                                                is_buy     BOOL,
                                                is_limit   BOOL,
                                                market     INT4 REFERENCES market )""")

            log.info("New database created.")
        else:
            log.info("Database exists, creating connection.")
            self.conn = await self.connect()

        await admin_conn.close()

    async def execute(self, query):
        self.conn.execute(query)
