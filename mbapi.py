#!usr/bin/python2.7
# GPL v3.

import json
import time


def flowenabled(title, site):
    """Find whether Flow is enabled on a given page.
    Parameters:
        title   :   a string containing the page title
        site    :   a mwclient Site object associated with the page

    Returns:
        True    if Flow is enabled on the page
        False   if Flow is not enabled on the page
        None    if the page does not exist
    """
    query = site.api(action = 'query',
                     titles = title,
                     prop = 'flowinfo')
    pagedict = query['query']['pages']
    for page in pagedict:
        if page == '-1':
            return None
        else:
            return (u'enabled' in pagedict[page]['flowinfo']['flow'])


def getpagecreator(title, site):
    """ Retrieve user information for the user who made the first edit
    to a page.
    Parameters:
        title   :   a string containing the page title
        site    :   a mwclient Site object associated with the page

    Returns:
        user    :   a string containing the page creator's user name
        userid  :   a string containing the page creator's userid
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


def getnewmembers(categoryname, site, timelastchecked):
    """ Data for the following API call: 
    """
    recentkwargs = {'action': 'query',
                    'list': 'categorymembers',
                    'cmtitle': categoryname,
                    'cmprop': 'ids|title|timestamp',
                    'cmlimit': 'max',
                    'cmsort': 'timestamp',
                    'cmdir': 'older',
                    'cmend': timelastchecked,
                    'continue': ''}
    result = site.api(**recentkwargs)
    newcatmembers = makelearnerlist(result)

    # I think this is an ok approach but I think this leads to weirdness with the learner list (first one gets run twice?)
    while True:
        newkwargs = recentkwargs.copy()
        newkwargs['continue'] = result['continue']
        result = site.api(**newkwargs)
        newcatmembers = makelearnerlist(result, newcatmembers)
        if 'continue' not in result:
            break
        
    return newcatmembers


def makelearnerlist(result, catusers=[]):
    """Create a list of dicts containing information on each user from
    the getnewmembers API result.

    Optional parameter: catusers
    """
    for page in result['query']['categorymembers']:
        userdict = {'profileid': page['pageid'],
                    'profile': page['title'],
                    'cattime': page['timestamp'],
                    'category': categoryname}
        catusers.append(userdict)
    return catusers


def getallcatmembers(category, site):
    """
    """
    kwargs = {'action': 'query',
              'list': 'categorymembers',
              'cmtitle': category,
              'cmprop': 'ids|title',
              'cmlimit': 'max',
              'continue': ''}
    result = site.api(**kwargs)
    catmembers = addmentorinfo(result)

    # continue shenanigans go here
    return catmembers

# TODO!
def addmentorinfo(result, catmembers=[]):
    """ TODO
    """
    for page in query['query']['categorymembers']:
        userdict = {'profileid': page['pageid'], 'profile': page['title']}
        catmembers.append(userdict)
    return catmembers

def postflow(page, topic, message, site):
    """Post a new topic to a Flow board.
    Parameters:
        page    :   string containing the title of the page to post to
        topic   :   string containing the new Flow topic
        message :   string containing the message to post in the topic
        site    :   logged-in mwclient Site object corresponding to
                    the page
    Returns the API POST result as a dictionary containing the post's
    metadata.

    If the bot has the appropriate permissions, this will create Flow
    boards on empty pages.
    """
    token = site.get_token('csrf')
    kwargs = {'action': 'flow',
              'page': page,
              'submodule': 'new-topic',
              'token': token,
              'nttopic': topic,
              'ntcontent': message,
              'ntmetadataonly': 'true'}
    query = site.api(**kwargs)
    return query
