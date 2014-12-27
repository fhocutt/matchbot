import logging
import os
import sys
import sqlalchemy as sqa

logpath = os.path.join(sys.argv[1], 'log')
print logpath

# FIXME DRY
def logrun(run_time, edited_pages, wrote_db, logged_errors):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    message = '{0}\tEdited: {1}\tDB write: {2}\tErrors: {3}'.format(run_time,
                  edited_pages, wrote_db, logged_errors)
#    formatter = logging.Formatter('%(asctime)s %(message)s')
    handler = logging.handlers.RotatingFileHandler(os.path.join(logpath, 'matchbot.log'),
                                                   maxBytes=10000,
                                                   backupCount=2)
#    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info(message)

# FIXME ditto
def logerror(message):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    handler = logging.FileHandler(os.path.join(logpath, 'matchbot_errors.log'))
    logger.addHandler(handler)
    logger.error(message)

# TODO
def logmatch(luid, lprofile, category, muid, matchtime,
                  cataddtime, matchmade, run_time, revid=None, postid=None):
    engine = sqa.create_engine('sqlite:///matches.db', echo=True)
    metadata = sqa.MetaData()
    matches = sqa.Table('matches', metadata, autoload=True,
                        autoload_with=engine)
    ins = matches.insert()
    conn = engine.connect()
    conn.execute(ins, {'luid': luid, 'lprofile': lprofile,
                       'category': category, 'muid': muid,
                       'matchtime':matchtime, 'cataddtime': cataddtime,
                       'revid': revid, 'postid': postid,
                       'matchmade': matchmade, 'run_time': run_time})
    return True

def logdebug(message):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    handler = logging.FileHandler(os.path.join(logpath, 'matchbot_debug.log'))
    logger.addHandler(handler)
    logger.debug(message)
