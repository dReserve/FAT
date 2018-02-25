""" The FATStack data server

This process collects and stores trade information from exchanges and serves
it to other FATStack processes.

"""

import fatstack.core
import psycopg2
import krakenex

class DataServer:
    def __init__(self, args):
        print('Getting pairs.')
        kraken = krakenex.API()
        pairs = kraken.query_public('AssetPairs')['result']
        


        print('Conencting to the database.')
        db = psycopg2.connect(dbname=args.dbname, user=args.dbuser, host='localhost', password=args.dbpwd)

        cur = db.cursor()

        # cur.execute('CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);')
        # db.commit()

        cur.close()
        db.close()

        print(args)

def start_ds(args):
    ds = DataServer(args)
    # ds.loop()
    print(ds)
