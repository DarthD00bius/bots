The file bots.py contains the classes used by the main script.

Archive-Bot.py is the mains script.

Archive-Bot.ini contains configuration settings for Archive-Bot.py.
dbconn.ini contains configuration settings for the database Archive-Bot uses to store data.
PRAW.ini contains configuration settings for interacting with the reddit API.

This script was designed to work on PythonAnywhere, and assumes you have a MySQL database named archivebot, with one table called repliedTo. The script to create the table repliedTo is included.

This is my first reddit bot, my first Python project, and my first time using MySQL, so I wouldn't be surprised if it is full of poor coding practices. Please do not use any of my code as an example of the best way to accomplish something.

