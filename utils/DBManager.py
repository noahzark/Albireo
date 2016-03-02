from psycopg2.pool import ThreadedConnectionPool
import yaml


fr = open('../config/config.yml', 'r')
config = yaml.load(fr)

dbConfig = config['database']
dsn = ' '.join('%s=%s' % (k,v) for k,v in dbConfig.items())

# use thread safe connection pool
pool = ThreadedConnectionPool(1, config['poolConnections'], dsn)

def getConn():
    return pool.getconn()

def putConn(conn):
    pool.putconn(conn)
