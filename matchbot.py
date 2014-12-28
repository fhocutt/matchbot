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
import json

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


def parse_timestamp(t):
    if t == '0000-00-00T00:00:00Z':
        return None
    return datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')

def timelog(run_time):
    # get last time run and log time-started-running
    timelogfile = os.path.join(filepath, 'time.log')
    with open(timelogfile, 'r+b') as timelog:
        prevruntimestamp = timelog.read()
        timelog.seek(0)
        timelog.write(datetime.datetime.strftime(run_time,
                                                 '%Y-%m-%dT%H:%M:%SZ'))
        timelog.truncate()
    return prevruntimestamp

def getlearners(prevruntimestamp, site):
    learners = []
    # get the new learners for all the categories
    # info to start: profile page id, profile name, time cat added, category
    for category in lcats:
        try:
            newlearners = mbapi.newmembers(category, site, prevruntimestamp)
            for userdict in newlearners:
                # add the results of that call to the list of users?
                if userdict['profile'].startswith(prefix):
                    learners.append(userdict)
                else:
                    pass
        except (Exception):
            mblog.logerror('Could not fetch newly categorized profiles in {}'.format(category))
            logged_errors = True
    return learners

def getlearnerinfo(learners, site):
    # add information: username, userid, talk page id
    for userdict in learners:
        #figure out who it is
        learner, luid = mbapi.userid(userdict['profile'], site)
        userdict['learner'] = learner
        userdict['luid'] = luid
    return learners

def getmentors(site):
    # find available mentors
    mentors = {}
    nomore = mbapi.getallmembers(NOMENTEES, site)
    allgenmentors = mbapi.getallmembers(CATCHALL, site)
    genmentors = [x for x in allgenmentors if x not in nomore and x['profile'].startswith(prefix)]
    for category in mcats:
        try:
            catmentors = mbapi.getallmembers(category, site)
            mentors[category] = [x for x in catmentors if x not in nomore and x['profile'].startswith(prefix)]
        except(Exception):
            mblog.logerror('Could not fetch list of mentors for {}'.format(category))
    return (mentors, genmentors)

def match(catmentors, genmentors):
    """ Given two lists, returns a random choice from the first, or if there
    are no elements in the first returns a random choice for the second.
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
    """Puts the string together that can be posted to a talk page or
       Flow board to introduce a potential mentor to a learner.
    """
    greetings = config['greetings']
    if matchmade:
        greeting = greetings['matchgreeting'].format(learner, mentor, skill)
        topic = greetings['matchtopic']
    else:
        greeting = greetings['nomatchgreeting']
        topic = greetings['nomatchtopic']
    return (greeting, topic)

# FIXME handle namespace errors?
def gettalkpage(profile):
    talkpage = talkprefix + profile.lstrip(prefix)
    return talkpage

def postinvite(pagetitle, greeting, topic, flowenabled):
    """ Given a page, posts a greeting. If Flow is enabled or the page
        does not already exist, posts as a new topic on a the page's
        Flow board; otherwise, appends the greeting to the page's existing
        text.
    """
    if flowenabled:
        result = mbapi.postflow(pagetitle, topic, greeting, site)
        return result
    else:
        profile = site.Pages[pagetitle]
#        if flowenabled == None:
#            result = mbapi.postflow(pagetitle, greeting, topic, site)
#            return result
#        else:
        newtext = '{0}\n\n=={1}==\n{2}'.format(profile.text(), topic, greeting)
        result = profile.save(newtext, summary=topic)
        return result
    return False

def getrevid(result, isflow):
    if isflow:
        return (None, result['flow']['new-topic']['committed']['topiclist']['post-revision-id'])
    else:
        return (result['newrevid'], None)

# TODO Flow is changing
def gettimeposted(result, isflow):
    if isflow:
        return datetime.datetime.now() #FIXME (documentme)
    else:
        return result['newtimestamp']

if __name__ == '__main__':
    # To log
    run_time = datetime.datetime.utcnow()
    edited_pages = False
    wrote_db = False
    logged_errors = False

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

    learners = getlearnerinfo(getlearners(prevruntimestamp, site), site)
    mentors, genmentors = getmentors(site)

    for learner in learners:
        # make the matches, logging info
        try:
            mcat = mcat_dict[learner['category']]
            mentor = match(mentors[mcat], genmentors)
        except Exception as e:
            mblog.logerror('Matching failed for {}'.format(learner['learner']))
            logged_errors = True
            continue

        if mentor == None:
            mname, muid = mbapi.userid(DEFAULTMENTOR, site)
        else:
            mname, muid = mbapi.userid(mentor['profile'], site)
            matchmade = True


        talkpage = gettalkpage(learner['profile'])
        flowenabled = mbapi.flowenabled(talkpage, site)
        basecat = basecat_dict[learner['category']]
        greeting, topic = buildgreeting(learner['learner'], mname,
                                        basecat, matchmade)

        try:
            response = postinvite(talkpage, greeting, topic, flowenabled)
            edited_pages = True
        except Exception as e:
            print e
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
            print e
            mblog.logerror('Could not write to DB for {}'.format(learner['learner']))
            logged_errors = True
            continue

    mblog.logrun(run_time, edited_pages, wrote_db, logged_errors)
