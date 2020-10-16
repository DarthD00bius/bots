#!/usr/bin/env python
import praw
import os
import sys
import datetime
import bots
import configparser
import logging

###################################################
#initialize config settings
###################################################
scriptname = "ArchiveBot"
configname = scriptname + ".ini"

#set default values in case there is no config file
logpath = ""
dataconfigpath= ""
loglevel = logging.INFO
botversion = "0.1"
maintainerdm = "your reddit username"
maxcommentlength = 9999
maxhoursold = 2
botname = "bot's reddit username"
subreddits = "comma-separated list of subreddits you want to work in"
botversion = "0.01"
configpath = ""
logpath = configpath
sqlconfigpath = configpath
sqlconfigname = "dbconn.ini"

#Look in a few possible locations for the main config file. Use the first one found.
defaults = []
defaults.append("")       #current working directory
defaults.append("~/")
defaults.append(scriptname + "/")
defaults.append("~/" + scriptname + "/") 
defaults.append("bots/")
defaults.append("~/bots/")
defaults.append("~/config/")

for d in defaults:
    #find the first file
    if os.path.isfile(d + configname):
        configpath = d
        break

configfile = configpath + configname
print("Attempting to load from configfile {}".format(configfile ))
# read main config file
with open(configfile ) as f:
    try:
        config = configparser.RawConfigParser()
        config.read_file(f)
        f.close()

    except config.Error as err:
        print("ERROR: Error reading config file {}".format(configpath + configname))
        print(err)
        f.close()
        sys.exit(1)

#extract config data
#All the variable names are hardcode in the script, and the below logic looks for a variable with the same name in the config file.
sec="Main"

if config.has_section(sec):
    #script name - used for naming log
    if config.has_option(sec, "scriptname"):
        scriptname = config.get(sec,  "scriptname")
    
    #data source config path
    if config.has_option(sec,  "dataconfigpath"):
        sqlconfigpath = config.get(sec,  "dataconfigpath")
    elif config.has_option(sec,  "sqlconfigpath"):
        sqlconfigpath = config.get(sec,  "sqlconfigpath")
    else:
        sqlconfigpath = configpath

    #database name
    if config.has_option(sec,  "dbname"):
        sqlconfigpath = config.get(sec,  "dataconfigpath")
    elif config.has_option(sec,  "sqlconfigpath"):
        sqlconfigpath = config.get(sec,  "sqlconfigpath")
    else:
        sqlconfigpath = configpath        

    #log path
    if config.has_option(sec,  "logpath"):
        logpath = config.get(sec ,  "logpath")
    elif config.has_option(sec,  "log"):
        logpath = config.get(sec ,  "log")
    else:
        logpath = ""

    #logging level
    loglevel = logging.WARNING
    if config.has_option(sec,  "loglevel"):
        l = config.get(sec,  "loglevel").upper()
        if l == "DEBUG":
            loglevel = logging.DEBUG
        elif l == "INFO":
            loglevel = logging.INFO
        else:
            loglevel = logging.WARNING

    #version
    if config.has_option(sec,  "botversion"):
        botversion = config.get(sec,  "botversion")

    #subreddit to check
    if config.has_option(sec, "subreddits"):
        subreddits = config.get(sec,"subreddits")

    #reddit settings
    if config.has_option(sec,  "maintainerdm"):
        maintainerdm = config.get(sec,  "maintainerdm")
    if config.has_option(sec,  "maxcommentlength"):
        maxCommentLen = int(config.get(sec,  "maxcommentlength"))
    if config.has_option(sec,  "maxhoursold"):
        maxAgeHours = int(config.get(sec,  "maxhoursold"))
    if config.has_option(sec,  "botname"):
        botname = config.get(sec,  "botname")

else:
    print("Config not loaded.")

# convert hours to seconds
maxAge = maxAgeHours * 60 * 60

#set up logging
logfile = logpath + scriptname + datetime.datetime.now().strftime("%Y%m%d%H%M%S") +  ".log"
#determine path for log
if not os.path.exists(logpath):      #symlinks allowed
    try:
        os.makedirs(logpath)
    except:
        logpath = ""

print("logfile={}".format(logfile))
logging.basicConfig(filename=os.path.abspath(logfile),level=loglevel)

###################################################
#set up database conneciton
###################################################
sqlconfigfile = sqlconfigpath + "dbconn.ini"
logging.debug("sqlconfigfile={}".format(sqlconfigfile))
if not os.path.isfile(sqlconfigfile):
    print("sqlconfig file {} not found.".format(sqlconfigfile))
    logging.error("sqlconfig file {} not found.".format(sqlconfigfile))
    sys.exit(1)

dataStorage = bots.DataHandler(sqlconfigfile, scriptname)

###################################################
#  Make a template for replies
###################################################
template = "%SALUTATION% %BODY% %FOOTER%"
sep = "\n \n --- \n \n "
timezone = "GMT"
salutation = "Posted by /u/%OP%.  Archived by {} at %ReplyTime% {}.".format(botname,  timezone) + sep
footer_body = "{} version {}. | [Contact Bot Maintainer](/u/{}) ".format(botname, botversion, maintainerdm)
footer = sep + footer_body
maxQuotedLen = maxCommentLen - len(salutation + "  " + footer)
logging.debug("maxQuotedLen={}".format(maxQuotedLen))

###################################################
#Create reddit instance
###################################################
#set up PRAW logging
handler = logging.StreamHandler()
handler.setLevel(loglevel)
logger = logging.getLogger('prawcore')
logger.setLevel(loglevel)
logger.addHandler(handler)

logging.info("Trying to create reddit instance")
try:
    logging.debug("reddit = praw.Reddit({})".format(scriptname))
    reddit = praw.Reddit(scriptname)
except praw.exceptions.PRAWException as exc:
    print("PRAW Exception")
    logging.error("PRAW ERROR: {} : {} in field {}".format( exc.error_type, exc.message, exc.field))

logging.info("Success.")
logging.debug("Reddit user: {}".format(reddit.user.me()))

###################################################
#import list of posts we've already replied to
###################################################
repliedList = []
repliedList = dataStorage.retrieve("repliedTo")

###################################################
#import list of subreddits to run on
###################################################
subList = subreddits.split(",")

###################################################
# Main action
###################################################
def ArchivePost(p):
    time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    OP = p.author.name
    title = p.title
    text = p.selftext
    logging.debug("OP={}".format(OP))
    sal = salutation
    sal = sal.replace("%OP%",  OP)
    sal = sal.replace("%ReplyTime%",  time)
    body = "\n\n> **{}**\n\n>".format(title) + text.replace("\n",  "\n>")
    if len(body) > maxQuotedLen:
        body = body[0:maxQuotedLen]
    result = template
    result = result.replace("%SALUTATION%",  sal)
    result =  result.replace("%FOOTER%", footer)
    result =  result.replace("%BODY%",  body)
    return result

#Check subreddits for text submissions to archive
newreplies = []
lim=100

logging.debug("Checking subreddits for text submissions to archive")
for subredditname in subList:
    logging.debug("Checking subreddit {}.".format(subredditname))
    try:
        subreddit = reddit.subreddit(subredditname)
    except praw.exceptions.APIException as exc:
        logging.error(exc.error_type + " : " + exc.message + "in field " + exc.field)

    currentTime = datetime.datetime.now().timestamp()
    cutoffTime = currentTime - maxAge
    logging.debug("CutoffTime={}. currentTime={}".format(cutoffTime,  currentTime))
    logging.debug("Checking for new posts in {}.".format(str(subreddit)))
    for post in subreddit.new(limit=lim):
        #for each post that's not too old
        if post.is_self and post.created_utc > cutoffTime and post.author.name != "AutoModerator":
            logging.debug("Post id {} has created time of {}".format(str(post.id),  str(post.created_utc)))
            #For each one this bot hasn't replied to yet
            if post.id not in repliedList:
                replyBody = ArchivePost(post)
                logging.info("Replying to post {} ".format(post.id))
                try:
                    post.reply(replyBody)
                except praw.exceptions.APIException as exc:
                    logging.error(exc.error_type + " : " + exc.message + "in field " + exc.field)
                # add to list of posts archived
                newreplies.append(post.id)

        logging.debug("Finished checking for new posts in subreddit {}.".format(subredditname))

logging.debug("Finished checking subreddits for posts to archive.")


###################################################
# Write our updated list back to the db
###################################################
if len(newreplies) > 0:
    logging.debug("Storing replies.")
    dataStorage.store("repliedTo", newreplies)
else:
    logging.debug("No replies to store")







