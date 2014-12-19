import sqlalchemy as sqa
import datetime

def createtable():
    engine = sqa.create_engine('sqlite:///matches.db', echo=True)
    metadata = sqa.MetaData()
    matches = sqa.Table('matches', metadata,
                        sqa.Column('id', sqa.Integer, primary_key = True),
                        sqa.Column('luid', sqa.Integer),
                        sqa.Column('lprofile', sqa.Integer),
                        sqa.Column('category', sqa.String),
                        sqa.Column('muid', sqa.Integer),
                        sqa.Column('matchtime', sqa.DateTime),
                        sqa.Column('cataddtime', sqa.DateTime),
                        sqa.Column('revid', sqa.Integer),
                        sqa.Column('postid', sqa.Integer),
                        sqa.Column('matchmade', sqa.Boolean),
                        sqa.Column('runid', sqa.Integer))

    metadata.create_all(engine)

def insertmatches(luid, lprofile, category, muid, matchtime,
                  cataddtime, matchmade, runid, revid=None, postid=None):
    engine = sqa.create_engine('sqlite:///matches.db', echo=True)
    metadata = sqa.MetaData()
    matches = sqa.Table('matches', metadata, autoload=True,
                        autoload_with=engine)
    ins = matches.insert()
    conn = engine.connect()
    conn.execute(ins, {'luid': luid, 'lprofile': lprofile,
                       'category': category, 'muid': muid,
                       'matchtime':matchtime, 'cataddtime': cataddtime,
                       'revid': revid, 'postid': postid, 'matchmade':
                       matchmade, 'runid': runid})

def main():
    createtable()
    insertmatches(123, 234, 'coding', 345, datetime.datetime.now(),
                  datetime.datetime.now(), True, 456, postid=6577)


if __name__ == '__main__':
    main()
