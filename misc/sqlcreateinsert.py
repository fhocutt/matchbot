import sqlalchemy as sqa
import datetime
from load_config import config

def makeconnstr():
    username = config['dbinfo']['username']
    password = config['dbinfo']['password']
    host = config['dbinfo']['host']
    dbname = config['dbinfo']['dbname']
    conn_str = 'mysql://{}:{}@{}/{}'.format(username, password, host, dbname)
    return conn_str

def createtable(conn_str):
    engine = sqa.create_engine(conn_str, echo=True)
    metadata = sqa.MetaData()
    matches = sqa.Table('matches', metadata,
                        sqa.Column('id', sqa.Integer, primary_key = True),
                        sqa.Column('luid', sqa.Integer),
                        sqa.Column('lprofileid', sqa.Integer),
                        sqa.Column('category', sqa.String(75)),
                        sqa.Column('muid', sqa.Integer),
                        sqa.Column('matchtime', sqa.DateTime),
                        sqa.Column('cataddtime', sqa.DateTime),
                        sqa.Column('revid', sqa.Integer),
                        sqa.Column('postid', sqa.String(50)),
                        sqa.Column('matchmade', sqa.Boolean),
                        sqa.Column('run_time', sqa.DateTime))
    metadata.create_all(engine)

def insertmatches(conn_str, luid, lprofileid, category, muid, matchtime,
                  cataddtime, matchmade, run_time, revid=None, postid=None):
    engine = sqa.create_engine(conn_str, echo=True)
    metadata = sqa.MetaData()
    matches = sqa.Table('matches', metadata, autoload=True,
                        autoload_with=engine)
    ins = matches.insert()
    conn = engine.connect()
    conn.execute(ins, {'luid': luid, 'lprofileid': lprofileid,
                       'category': category, 'muid': muid,
                       'matchtime':matchtime, 'cataddtime': cataddtime,
                       'revid': revid, 'postid': postid, 'matchmade':
                       matchmade, 'run_time': run_time})

def main():
    conn_str = makeconnstr()
    createtable(conn_str)
#    insertmatches(conn_str, 123, 234, 'coding', 345, datetime.datetime.now(),
#                  datetime.datetime.now(), True, datetime.datetime.now(), postid=6577)


if __name__ == '__main__':
    main()
