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
# Test category tags: 
#   Co-op (maybe not necessary because implied by subpage status?)
#   Co-op mentor
#   Co-op Learner
#   Teaches research
#   Teaches editing
#   Teaches template writing
#   Wants to do research
#   Wants to edit
#   Wants to write templates
#
# For each page tagged "Co-op learner", MatchBot v0.1.0 leaves a message on
# the corresponding talk page with the name of a possible mentor (one for
# each learning interest category on the page).

import random
import datetime
import logging
import logging.handlers
import ConfigParser
import sys

import sqlalchemy
import mwclient

# Config file with login information and user-agent string
import matchbot_settings
import mberrors
import mbapi
import mblog


# TODO: Consider whether these should be kept here or in a config file
mcats = ['Category:Co-op/Mentors/Communication',
               'Category:Co-op/Mentors/Writing',
               'Category:Co-op/Mentors/Other']
CATCHALL = 'Category:Co-op/Mentors/General'
NOMENTEES = 'Category:Co-op/Inactive mentors'
lcats = ['Category:Co-op/Requests/Communication',
                'Category:Co-op/Requests/Writing',
                'Category:Co-op/Requests/Other']
category_dict = {k:v for (k,v) in zip(lcats, mcats)}


# constants for run logs:
run_id = 0 # or sys.argv[1], depending on cron setup TODO
edited_pages = False
wrote_db = False
logged_errors = False

def parse_timestamp(t):
    if t == '0000-00-00T00:00:00Z':
        return None
    return datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ')

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
    if matchmade:
        greeting = 'Hello, [[User:%(l)s|%(l)s]]! Thank you for your interest '\
                   'in the Co-op. [[User:%(m)s|%(m)s]] has listed "%(s)s" in '\
                   'their mentorship profile. '\
                   'Leave them a message on their talk page and see if you '\
                   'want to work together!' % {'l': learner, 'm': mentor,
                                               's': skill}
        topic = 'Welcome to the Co-op! Here is your match.'
    else:
        greeting = 'Sorry, we don\'t have a match for you!'
        topic = 'Welcome to the Co-op!'
    return (greeting, topic)

# FIXME handle namespace errors?
def gettalkpage(profile):
    talkpage = 'Wikipedia talk:' + profile.lstrip('Wikipedia:')
    return talkpage

def postinvite(pagetitle, greeting, topic, flowenabled):
    """ Given a page, posts a greeting. If Flow is enabled or the page
        does not already exist, posts as a new topic on a the page's
        Flow board; otherwise, appends the greeting to the page's existing
        text.
    """
    if flowenabled:
        # TODO: result format is in flux right now, may return metadata later
        result = mbapi.postflow(pagetitle, topic, greeting, site)
        return result
    else:
        profile = site.Pages[pagetitle]
#        if flowenabled == None:
#            mbapi.postflow(pagetitle, greeting, topic)
#            return True
#        else:
        newtext = profile.text() + '\n\n' + greeting
        result = profile.save(newtext, summary=topic)
        return result
    return False

def getrevid(result, isflow):
    if isflow:
        return result['flow']['new-topic']['committed']['topiclist']['post-revision-id']
    else:
        return result['newrevid']

# TODO Flow is changing
def gettimeposted(result, isflow):
    if isflow:
        return datetime.datetime.now() #FIXME
    else:
        return result['newtimestamp']

if __name__ == '__main__':
    # get last time run and log time-started-running
    with open('time.log', 'r+b') as timelog:
        prevruntimestamp = timelog.read()
        timelog.seek(0)
        timelog.write(datetime.datetime.strftime(datetime.datetime.now(),
                                                 '%Y-%m-%dT%H:%M:%SZ'))
        timelog.truncate()

    # Initializing site + logging in
    try:
        site = mwclient.Site(('https', 'test.wikipedia.org'),
                              clients_useragent=matchbot_settings.useragent)
        site.login(matchbot_settings.username, matchbot_settings.password)
        mblog.logdebug('logged in as ' + matchbot_settings.username)
    except(mwclient.LoginError):
        mblog.logerror('LoginError: could not log in')
        logged_errors = True
    except(Exception):
        mblog.logerror('Login failed') # FIXME more verbose error plz
        logged_errors = True
        sys.exit()

    learners = []
    # get the new learners for all the categories
    # info to start: profile page id, profile name, time cat added, category
    for category in lcats:
        try:
            newlearners = mbapi.newmembers(category, site, prevruntimestamp) #FIXME this should have time
            for userdict in newlearners:
                # add the results of that call to the list of users?
                if userdict['profile'].startswith('Wikipedia:Co-op/'):
                    learners.append(userdict)
                else:
                    pass
        except (Exception):
            mblog.logerror('Could not fetch newly categorized profiles in %s' % 
                     category)
            logged_errors = True

    # add information: username, userid, talk page id
    for userdict in learners:
        #figure out who it is
        learner, luid = mbapi.userid(userdict['profile'], site)
        userdict['learner'] = learner
        userdict['luid'] = luid

    # find available mentors
    mentors = {}
    nomore = mbapi.getallmembers(NOMENTEES, site)
    allgenmentors = mbapi.getallmembers(CATCHALL, site)
    genmentors = [x for x in allgenmentors if x not in nomore and x['profile'].startswith('Wikipedia:Co-op/')]
    for category in mcats:
#        try:
        catmentors = mbapi.getallmembers(category, site)
        mentors[category] = [x for x in catmentors if x not in nomore]
#        except(Exception):
 #           mblog.logerror('Could not fetch list of mentors for %s') % category

# end up with a dict of lists of mentors, categories as keys.

    for learner in learners:
        # make the matches, logging info
        mcat = category_dict[learner['category']]
#        try:
        matchmade = False
        catments = mentors[mcat]
        mentor = match(catments, genmentors) # FIXME figure out category store
        if mentor == None:
            raise mberrors.MatchError
        mname, muid = mbapi.userid(mentor['profile'], site)
        matchmade = True
#        except (mberrors.MatchError):
            # add '[[Category:No match found]]' to their page
#            matchmade = False
#        except (Exception):
#            mblog.logerror('Matching/default match failed')
#            logged_errors = True
#            continue

        talkpage = gettalkpage(learner['profile'])
        flowenabled = mbapi.flowenabled(talkpage, site)
        basecat = learner['category'].lstrip('Category:Co-op/Requests/') #FIXME 
            # (basecat: there's something weird with "Communication", test this)
        greeting, topic = buildgreeting(learner['learner'], mname,
                                        basecat, matchmade)

#        try:
        response = postinvite(talkpage, greeting, topic, flowenabled) # return? test? TODO
        edited_pages = True
        revid = getrevid(response, flowenabled)
        postid = None
        matchtime = parse_timestamp(gettimeposted(response, flowenabled))

#        except (Exception):
#            mblog.logerror('Could not post match on page')
#            logged_errors = True
#            break

#        try:
        cataddtime = parse_timestamp(learner['cattime'])
        mblog.logmatch(luid=luid, lprofile=learner['profile'], muid=muid,
                           category=basecat, cataddtime=cataddtime,
                           matchtime=matchtime, matchmade=matchmade,
                           revid=revid, postid=postid, runid=run_id)
        wrote_db = True
#        except (Exception):
#            mblog.logerror('Could not write to DB')
#            logged_errors = True
#            break

    mblog.logrun(run_id, edited_pages, wrote_db, logged_errors)
