matchbot
========

MatchBot is a MediaWiki bot that runs in the
[Wikipedia Co-op](https://en.wikipedia.org/Wikipedia:Co-op), a space that fosters
mentorship and the sharing of skills needed to edit
[English Wikipedia](https://en.wikipedia.org). Co-op members and mentors are
identified by the presence of category tags on a profile page. MatchBot
inspects these categories to match mentors and learners, who are then free to
follow up with each other and start asking and answering questions.


## Getting started

To download with git:
```bash
$ git clone https://github.com/fhocutt/matchbot.git
```

Update `config.json` with your bot's login information and database
credentials, and make any other necessary changes (see 
[Configuring MatchBot](#Configuring MatchBot) for more information).

To create a database with the expected schema:
```bash
$ python path/to/matchbot/misc/sqlcreateinsert.py
```

To run the script manually:
```bash
$ python matchbot.py <path-to-config>
```

If you have installed this with `git clone` as above and are in the
`path/to/matchbot/` directory,
```bash
$ python matchbot.py .
```
will run the script.

MatchBot will not run if the directory specified in `<path-to-config>` does not
contain `config.json`, `time.log`, and a `logs/` folder.

## Dependencies

MatchBot has been developed and tested using the following versions of its
dependencies:
```
mwclient==0.7.2dev
SQLAlchemy==0.9.7
```

Notes:

* The development version of [mwclient](https://github.com/mwclient/mwclient)
  can be installed with pip:
```bash
$ pip install git+git://github.com/mwclient/mwclient.git
```
  The 0.7.1 version of mwclient should work as well but has not been tested yet.
* SQLAlchemy depends on MySQLdb. If unexpected errors are happening, they may
  be MySQLdb path errors.


## How matches are made
MatchBot's category-based matching algorithm is as follows:

* If possible, a Co-op member is matched with an available random mentor in the
  same category as the request (writing, best practices, etc.).
* If there is no available mentor with the skill, the member is matched with an
  available random mentor who has signed up to mentor in the "general skills"
  category.
* If there are no mentors available in either the relevant category or as
  general mentors, the Co-op maintainer is notified so that the maintainer can
  find a match manually and notify both people.

MatchBot assumes that:

* Every Co-op member/mentor will create their own profile page.
* Only sub-pages of [Wikipedia:Co-op](https://en.wikipedia.org/Wikipedia:Co-op)
  and [Wikipedia talk:Co-op](https://en.wikipedia.org/Wikipedia_talk:Co-op) are
  relevant to MatchBot's activity (queries or edits).
* Users will correctly tag their profiles with the correct categories, whether
  via manual edits or through the profile page creation gadget.
* Mentors who are not accepting new learners will manually add the opt-out
  category to their profile pages.
* That there will be a certain amount of oversight and manual intervention
  in correcting errors, handling missing matches, etc. from the Co-op
  maintainer.
* If a Co-op member's profile talk page does not exist when MatchBot tries to
  post a greeting, it will be created as a Flow board. Existing talk pages
  will be edited as usual.


## Configuring MatchBot

MatchBot keeps user-configurable information (login and database information,
text of the greetings to post, the default mentor to contact when a match is not
found, relevant category titles, and namespace/subpage information).

To change these settings, use a text editor to edit `config.json`. You should
add `config.json` to your `.gitignore` file to avoid accidentally uploading
your bot's credentials to your code repository. A sample configuration file is
provided.

JSON quirks:
* JSON expects no comma after the last item in a list. If you are getting
  mysterious JSON-related errors, check your lists.
* Only use double quotation marks, `"`.

### Configurable settings
#### Categories (`categories`):
As described in [How matches are made](#How matches are made), MatchBot uses
the presence or absence of categories on Co-op pages to match mentors and
learners. A mentor may opt out by adding the opt-out category to their profile
page. Requests for a mentor are made by placing one of the request categories
on a Co-op profile page. A mentor declares their mentorship interests by adding
one or more of the mentor categories to their Co-op profile.

All categories should include the "Category:" prefix.

* `general`: The category for mentors who are willing to mentor on any category.
* `optout`: The category for mentors who do not with to receive new matches.

The following three lists contain descriptions or categories corresponding to
the mentorship skills that the Co-op focuses on:

* `skillslist`: Short text descriptions of the skills
* `mentorcategories`: Category names used on mentor profile pages to offer
  mentorship in a skill
* `requestcategories`: Category names used on member profile pages to request
  instruction in a skill

There may be any number of skills/categories in these lists, but 
there *must* be the same number in each of them and each list *must* be in the
same order.


#### Database information (`dbinfo`):
`dbname`, `host`: Database name and host for the MySQL database you are using to log matches (see [Logging](#Logging)).


#### Default mentor (`defaultmentor`):
The title of the Co-op maintainer's profile page in the Co-op. This person will be notified if no match is possible.


#### Messages (`greetings`):
MatchBot edits Co-op profile talk pages to deliver matches. It has two types of
messages: one that is posted when a match is successfully made to notify the
Co-op member and their new mentor of the match, and one that is posted when no
match can be made and which welcomes the person and notifies the Co-op
maintainer.

topic is posted as the topic of the new Flow post (for Flow boards) and section header for normal talk pages, as well as the edit summary.

greeting is posted as the text of the Flow post or the section contents. The example one will generate an Echo notification for

`{0}`: The user name of the mentor
`{1}`: The skill requested ("communication", "general editing skills", etc.)

nomatchgreeting:
`{0}`: The user name of the Co-op maintainer

`noflowtemplate`: Template to add a new section and notify the learner. Designed to be used with both the match and no-match options.
`{0}`: Title for the new section
`{1}`: Requester's name (so they get an Echo notification)
`{2}`: Section text

*NOTE:* All `{N}`-type text listed above *must* be included in your messages,
no matter what other changes you make to the message text. For example, a
`nomatchgreeting` string that does not contain "`{0}`" is not valid and will
lead to errors that prevent the message from being posted.


(link to flowbot usergroup and the user account must be in the flowbot user group to post flow pages; but it'll work with normal pages)

#### Login information (`login`)

* `username`, `password`: Your bot's username and password.
* `protocol`: `http` or `https`. `https` is more secure and is recommended if
  the wiki supports it.
* `site`: the URL of the wiki the bot runs on (for instance, `en.wikipedia.org`
  for [English Wikipedia](https://en.wikipedia.org))
* `useragent`: Information about your bot. When running on WMF-run wikis, it
  must contain your bot's user name and a way to contact the person responsible
  for running it. For more information, see the [User-agent policies](http://meta.wikimedia.org/wiki/User-Agent_policy).


#### Namespace/root page/prefixes (`pages`):
MatchBot operates on sub-pages of the main Co-op page and of its associated talk
page.

* `main`: Title of the main page. All Co-op profile pages are sub-pages of this
  page.
* `talk`: Title of the main talk page. All Co-op profile talk pages are sub-
  pages of this page.


## Logging
MatchBot logs information every time it is run. All log files are stored in
`path/to/matchbot/logs/`.

### Runs

Information about each time the bot runs is logged to the `matchbot.log` text
file: the date and time the script was run, whether the script successfully
edited one or more pages, successfully logged information on one or more
matches to the associated relational database, and whether any errors were
handled while the script ran.

Example line in `matchbot.log`:
```
INFO 2015-01-01 01:00:45.650401 Edited: False Wrote DB: False Errors: False
```
To cap the size of these files, a new log file is started every 30 days. Two
backup logs are kept, each for 60 days.

### Matches

Information about matches is logged to a relational database. 

The schema for the appropriate sqlite3 backend is:
```sql
sqlite> .schema
CREATE TABLE matches (
    id INTEGER NOT NULL,
    luid INTEGER,
    lprofile INTEGER,
    category VARCHAR,
    muid INTEGER,
    matchtime DATETIME,
    cataddtime DATETIME,
    revid INTEGER,
    postid INTEGER,
    matchmade BOOLEAN,
    runid INTEGER,
    PRIMARY KEY (id)
);
```
Eventually MatchBot's match logging will only be backed by a MySQL database
on [Tool Labs](https://wikitech.wikimedia.org/wiki/Help:Tool_Labs).

### Errors

When possible, MatchBot simply logs errors and allows the script to continue.
Errors are logged to `matchbot_errors.log`. They include a stack trace for
all exceptions raised, including ones that are logged and handled so MatchBot
can finish a run.




TRY: create a co-op page with error traces instead of/in addition to email? Good idea.
make sure the maintainer is watching this
