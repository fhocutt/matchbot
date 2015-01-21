matchbot
========

MatchBot is a MediaWiki bot that runs in the
[Wikipedia Co-op](https://en.wikipedia.org/Wikipedia:Co-op), a space that fosters
mentorship and the sharing of skills. Co-op members and mentors are identified
by the presence of category tags on a profile page. MatchBot inspects these
categories to match mentors and learners so that these mentoring relationships
can begin.

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
  in correcting errors, handling missing matches, etc.

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
$ python path/to/matchbot/misc/sqlcreateinsert
```

To run the script manually:
```bash
$ python matchbot <path-to-config>
```

If you have installed this with `git clone` as above and are in the
`path/to/matchbot/` directory,
```bash
$ python matchbot .
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
  The 0.7.1 version of mwclient should work as well but has not been tested.
* SQLAlchemy depends on MySQLdb. If unexpected errors are happening, they may
  be due to problems with where MySQLdb is on the path.

## Configuring MatchBot

MatchBot keeps user-configurable information (login and database information,
text of greetings to post, the default mentor to contact when a match is not
found, relevant category titles, and namespace/subpage information).

To change these settings, use a text editor to edit `config.json`. You should
add `config.json` to your `.gitignore` file to avoid accidentally uploading
your credentials to your code repository.

Database information (`dbinfo`):

Messages: 
(warts: editing messages, string formatting)

Categories:

Default mentor:

Namespace/root page/prefixes:

Login information:

JSON quirks:

* JSON expects no comma after the last item in a list. If you are getting
  mysterious JSON-related errors, check your lists.
* Only use double quotation marks, `"`.

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
backup logs are kept at a time (each for 60 days).

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
    postid INTEGER, matchmade boolean, runid INTEGER, 
    PRIMARY KEY (id)
);
```
Eventually MatchBot's match logging will only be backed by a MySQL database
on [Tool Labs](https://wikitech.wikimedia.org/wiki/Help:Tool_Labs).

### Errors

Errors are logged to `matchbot_errors.log`. They include the stack trace for
all exceptions raised, including ones that are logged and handled so MatchBot
can finish its run.
