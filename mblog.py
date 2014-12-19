import logging
import sqlalchemy as sqa

# FIXME DRY
def logrun(run_id, edited_pages, wrote_db, logged_errors):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    message = '\t%s\t%s\t%s\t%s' % (run_id, edited_pages, wrote_db,
                                    logged_errors)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    handler = logging.handlers.RotatingFileHandler('matchbot.log',
                                                   maxBytes=100,
                                                   backupCount=2)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info(message)

# FIXME ditto
def logerror(message):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    handler = logging.FileHandler('matchbot_errors.log')
    logger.addHandler(handler)
    logger.error(message)

# TODO
def logmatch(luid, lprofile, category, muid, matchtime,
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
                       'revid': revid, 'postid': postid,
                       'matchmade': matchmade, 'runid': runid})
    return True

def logdebug(message):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(message)s')
    handler = logging.FileHandler('matchbot_debug.log')
    logger.addHandler(handler)
    logger.debug(message)
