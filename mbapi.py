#!usr/bin/python2.7
#
# Quick test script.
# Uses raw API calls through mwclient to test the Flow web API.
# Uses prop=flowinfo to see if Flow is enabled.
# Posts a new topic on a Flow board through action=flow&submodule=new-topic.
#
# GPL v3.

import json
import time
import mwclient
import flow_mw_settings as mwcreds

def flowenabled(title, site):
    """Given a string with the page title, return True if Flow is enabled"""
    query = site.api(action = 'query',
                     titles = title,
                     prop = 'flowinfo')
    print(query)
    pagedict = query['query']['pages']
    for page in pagedict:
        if page == '-1':
            return None
        else:
            return (u'enabled' in pagedict[page]['flowinfo']['flow'])

# TODO: put this in place with logic (flow enabled or not), make it return
def postflow(page, topic, message, site):
    """testing posting a new Flow topic through the API"""
    token = site.get_token('csrf')
    cooptitle = 'Wikipedia:Co-op/Mentorship match'
    kwargs = {'action': 'flow',
              'page': cooptitle,
              'submodule': 'new-topic',
              'token': token,
              'nttopic': topic,
              'ntcontent': message,
              'ntmetadataonly': 'true'}
    query2 = site.api(**kwargs)
    return query2

def userid(title, site):
    """ Returns the user who made the first edit to a page.

    Given a string with the page title, returns (user, userid)

    # /w/api.php?action=query&prop=revisions&format=json&rvdir=newer&titles=Wikipedia%3ACo-op%2FPerson2
    """
    query = site.api(action = 'query',
                     prop = 'revisions',
                     rvprop = 'user|userid',
                     rvdir = 'newer',
                     titles = title,
                     rvlimit = 1,
                     indexpageids = "")
    pagedict = query['query']['pages']
    for page in pagedict:
        user = pagedict[page]['revisions'][0]['user']
        userid = pagedict[page]['revisions'][0]['userid']
    return (user, userid)

# TODO: put in the call, make it return appropriately
def newmembers(categoryname, site, timelastchecked):
    """ Data for the following API call: """
    #   /w/api.php?action=query&list=categorymembers&format=json&cmtitle=Category%3AWants%20to%20edit&cmprop=ids|title|timestamp&cmlimit=max&cmsort=timestamp&cmdir=older&cmend=2014-11-05T01%3A12%3A00Z&indexpageids=
    recentkwargs = {'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': categoryname,
                    'cmprop': 'ids|title|timestamp',
                    'cmlimit': 'max',
                    'cmsort': 'timestamp',
                    'cmdir': 'older',
                    'cmend': timelastchecked}
    result = site.api(**recentkwargs)
    catusers = []
    for page in result['query']['categorymembers']:
        userdict = {'profileid': page['pageid'],
                    'profile': page['title'],
                    'cattime': page['timestamp'],
                    'category': categoryname}
        catusers.append(userdict)
    return catusers

#TODO
def getallmembers(category, site):
    kwargs = {'action': 'query',
              'list': 'categorymembers',
              'cmtitle': category,
              'cmprop': 'ids|title',
              'cmlimit': 'max'}
    query = site.api(**kwargs)
    catmembers = []
    for page in query['query']['categorymembers']:
        userdict = {'profileid': page['pageid'], 'profile': page['title']}
        catmembers.append(userdict)
    return catmembers



def savepage(page, addedtext, topic):
    """ uses Page.save() to save page, gets timestamp and new revid.
    format:
    {u'contentmodel': u'wikitext',
     u'newrevid': 219714,
     u'newtimestamp': u'2014-12-14T05:32:09Z',
     u'oldrevid': 218886,
     u'pageid': 68971,
     u'result': u'Success',
     u'title': u'Sandbox'}
    """
    newtext = page.text() + addedtext
    result = page.save(newtext, summary=topic)
    #TODO: if something weird happens here, or if there's nothing added, as {u'nochange': u'', u'contentmodel': u'wikitext', u'pageid': 68971, u'result': u'Success', u'title': u'Sandbox'}
    revtimestamp = result['newtimestamp']
    newrevid = result['newrevid']
    return (newrevid, revtimestamp)

if __name__ == '__main__':
    # Initializing site + logging in
    site = mwclient.Site(('https', 'test.wikipedia.org'),
                         clients_useragent=mwcreds.useragent)
    site.login(mwcreds.username, mwcreds.password)
    print("You are logged in as %s." % mwcreds.username)

    userid('Wikipedia:Co-op/Person2')
    print(flowenabled('Wikipedia:Co-op/Mentorship match'))
