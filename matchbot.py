# MatchBot is MediaWiki bot that finds and notifies entities of matches
# based on categories on profile pages. It will be incorporated into the en.wp
# Co-op program and should be able to be extended to match people with projects
# in the IdeaLab.
#
# Released under GPL v3.
#
# MatchBot currently runs in this test space: 
# https://test.wikipedia.org/wiki/Wikipedia:Co-op
#
# All mentor and learner profile pages are subpages of Wikipedia:Co-op.
#
# For each page tagged "Co-op learner", MatchBot v0.1.0 leaves a message on
# the corresponding talk page with the name of a possible mentor (one for
# each learning interest category on the page).

import random
import datetime
import sys
import os

import sqlalchemy
import mwclient

import mberrors
import mbapi
import mblog
from load_config import filepath, config


lcats = config['pages']['lcats']
mcats = config['pages']['mcats']
basecats = config['pages']['basecats']
prefix = config['pages']['prefix']
talkprefix = config['pages']['talkprefix']
NOMENTEES = config['pages']['NOMENTEES']
CATCHALL = config['pages']['CATCHALL']
DEFAULTMENTOR = config['defaultmentor']
mcat_dict = {k: v for (k, v) in zip(lcats, mcats)}
basecat_dict = {k: v for (k, v) in zip(lcats, basecats)}

# To log
run_time = datetime.datetime.utcnow()
edited_pages = False
wrote_db = False
logged_errors = False


def parse_timestamp(t):
    """Parse MediaWiki-style timestamps and return a datetime."""
    if t == '0000-00-00T00:00:00Z':
        return None
    return datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')

def timelog(run_time):
    """Get the timestamp from the last run, then log the current time
    (UTC).
    """
    timelogfile = os.path.join(filepath, 'time.log')
    with open(timelogfile, 'r+b') as timelog:
        prevruntimestamp = timelog.read()
        timelog.seek(0)
        timelog.write(datetime.datetime.strftime(run_time,
                                                 '%Y-%m-%dT%H:%M:%SZ'))
        timelog.truncate()
    return prevruntimestamp

def getlearners(prevruntimestamp, site):
    """Get a list of learners who have created profiles since the last
    time this script started running.

    Returns a list of dictionaries, each containing the learner's
    profile pageid, the profile page title, the category, and the
    timestamp corresponding to when the category was added.

    If it is not possible to retrieve the new profiles in a given
    category, it skips that category and logs an error.
    """
    learners = []
    for category in lcats:
        try:
            newlearners = mbapi.getnewmembers(category, site,
                                              prevruntimestamp)
            for userdict in newlearners:
                # Check that the page is actually in the Co-op
                if userdict['profile'].startswith(prefix):
                    learners.append(userdict)
                else:
                    pass
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Could not fetch newly categorized profiles in {}'.format(category))
            logged_errors = True
    return learners


def getlearnerinfo(learners, site):
    """Given a list of dicts containing information on learners, add
    the learner's username and userid to the corresponding dict. Return
    the changed list of dicts.

    Assumes that the owner of the profile created the profile.
    """
    for userdict in learners:
        try:
            learner, luid = mbapi.getpagecreator(userdict['profile'], site)
            userdict['learner'] = learner
            userdict['luid'] = luid
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Could not get information for {}'.format(userdict['profile']))
            logged_errors = True
            continue
    return learners


def getmentors(site):
    """Using the config data, get lists of available mentors for each
    category, filtering out mentors who have opted out of new matches.

    Return:
        mentors     : dict of lists of mentor names, keyed by mentor
                        category
        genmentors  : list of mentor names for mentors who will mentor
                        on any topic

    Assumes that the owner of the profile created the profile.
    """
    mentors = {}

    nomore = mbapi.getallcatmembers(NOMENTEES, site)
    allgenmentors = mbapi.getallcatmembers(CATCHALL, site)
    genmentors = [x for x in allgenmentors if x not in nomore and
                  x['profile'].startswith(prefix)]
    for category in mcats:
        try:
            catmentors = mbapi.getallcatmembers(category, site)
            mentors[category] = [x for x in catmentors if x not in nomore and
                                 x['profile'].startswith(prefix)]
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Could not fetch list of mentors for {}'.format(category))
            logged_errors = True
            continue
    return (mentors, genmentors)

def match(catmentors, genmentors):
    """Given two lists, return a random choice from the first, or if there
    are no elements in the first return a random choice from the second.
    If there are no elements in either return None.
    """
    if catmentors:
        mentor = random.choice(catmentors)
        return mentor
    elif genmentors:
        mentor = random.choice(genmentors)
        return mentor
    else:
        return None

def buildgreeting(learner, mentor, skill, matchmade):
    """Create a customized greeting string to be posted to a talk page
    or Flow board to introduce a potential mentor to a learner.

    Return the greeting and a topic string for the greeting post.
    """
    greetings = config['greetings']
    if matchmade:
        greeting = greetings['matchgreeting'].format(learner, mentor, skill)
        topic = greetings['matchtopic']
    else:
        greeting = greetings['nomatchgreeting']
        topic = greetings['nomatchtopic']
    return (greeting, topic)

def getprofiletalkpage(profile):
    """Get the talk page for a profile (a sub-page of the Co-op)."""
    talkpage = talkprefix + profile.lstrip(prefix)
    return talkpage

def postinvite(pagetitle, greeting, topic, flowenabled):
    """Post a greeting, with topic, to a page. If Flow is enabled or
    the page does not already exist, post a new topic on a the page's
    Flow board; otherwise, appends the greeting to the page's existing
    text.

    Return the result of the API POST call as a dict.
    """
    if flowenabled:
        result = mbapi.postflow(pagetitle, topic, greeting, site)
        return result
    else:
        profile = site.Pages[pagetitle]
        if profile.text == '':
            result = mbapi.postflow(pagetitle, greeting, topic, site)
            return result
        else:
            newtext = '{0}\n\n=={1}==\n{2}'.format(profile.text(), topic, greeting)
            result = profile.save(newtext, summary=topic)
            return result
    return None

def getrevid(result, isflow):
    """ Get the revid (for a non-Flow page) or the post-revision-id
    (for a Flow page), given the API result for the POST request.

    Return a tuple (revid, post-revision-id). Either revid or
    post-revision-id will be None.
    """
    if isflow:
        return (None, result['flow']['new-topic']['committed']['topiclist']['post-revision-id'])
    else:
        return (result['newrevid'], None)

def gettimeposted(result, isflow):
    """Get the time a revision was posted from the API POST result, if
    possible.

    If the page has Flow enabled, the time posted will be approximate.

    If the page does not have Flow enabled, the time will match the
    time in the wiki database for that revision.
    """
    if isflow:
        return datetime.datetime.utcnow()
    else:
        return result['newtimestamp']

if __name__ == '__main__':
    # Get last time run, save time of run to log
    prevruntimestamp = timelog(run_time)

    # Initializing site + logging in
    login = config['login']
    try:
        site = mwclient.Site((login['protocol'], login['site']),
                              clients_useragent=login['useragent'])
        site.login(login['username'], login['password'])
        mblog.logdebug('logged in as ' + login['username'])
    except mwclient.LoginError as e:
        mblog.logerror('{0}. Login failed for {1}'.format(e, login['username']))
        logged_errors = True
        sys.exit()

    # create a list of learners who have joined since the previous run
    learners = getlearnerinfo(getlearners(prevruntimestamp, site), site)
    mentors, genmentors = getmentors(site)

    for learner in learners:
        try:
            mcat = mcat_dict[learner['category']]
            mentor = match(mentors[mcat], genmentors)
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Matching failed for {}'.format(learner['learner']))
            logged_errors = True
            continue

        try:
        # if there is no match, leave a message with the default mentor but do
        # not record a true match
            if mentor == None:
                mname, muid = mbapi.getpagecreator(DEFAULTMENTOR, site)
            else:
                mname, muid = mbapi.getpagecreator(mentor['profile'], site)
                matchmade = True
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Could not get information for profile {}'.format(mentor['profile']))
            logged_errors = True
            continue

        try:
            talkpage = getprofiletalkpage(learner['profile'])
            flowenabled = mbapi.flowenabled(talkpage, site)
            basecat = basecat_dict[learner['category']]
            greeting, topic = buildgreeting(learner['learner'], mname,
                                            basecat, matchmade)
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Could not create a greeting for {}'.format(learner['learner']))
            logged_errors = True
            continue

        try:
            response = postinvite(talkpage, greeting, topic, flowenabled)
            edited_pages = True
        except Exception as e:
            print e  # FIXME
            mblog.logerror('Could not post match on {}\'s page'.format(learner['learner']))
            logged_errors = True
            continue

        try:
            revid, postid = getrevid(response, flowenabled)
            matchtime = parse_timestamp(gettimeposted(response, flowenabled))
            cataddtime = parse_timestamp(learner['cattime'])
            mblog.logmatch(luid=learner['luid'], lprofile=learner['profile'],
                           muid=muid, category=basecat, cataddtime=cataddtime,
                           matchtime=matchtime, matchmade=matchmade,
                           revid=revid, postid=postid, run_time=run_time)
            wrote_db = True
        except Exception as e: 
            print e  # FIXME
            mblog.logerror('Could not write to DB for {}'.format(learner['learner']))
            logged_errors = True
            continue

    mblog.logrun(run_time, edited_pages, wrote_db, logged_errors)
