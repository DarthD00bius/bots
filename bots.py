import mysql.connector
import configparser
import logging
import datetime

###################################################
#  Class Definitions                                
###################################################
class Word:
    def __init__(self, mispelling, correction, alternate):
        self.misspelling = mispelling
        self.correction = correction
        self.alternate = alternate


class DataHandler:
       
    def __init__(self,  configpath,  botname):
        logging.debug("Starting _init_")
        self.path = configpath
        self.type = "mysql"
        self.scriptname = botname
        self.dbhost = ""
        self.dbuser = ""
        self.dbpassword = ""
        self.db = ""
        self.initSql()
        
    def initSql(self):
        ###################################################
        #Create database connection
        ###################################################
        #get db credentials and config
        #read config file
        #we are using RawConfigParser, meaning % interpolation won't work, but on the flipside, passwords can contain % characters
        sqlconfigpath = self.path
        with open(sqlconfigpath) as f:
            try:
                config = configparser.RawConfigParser()
                config.read_file(f)
                f.close()

            except config.Error as err: 
                logging.error("ERROR: Error reading config file sqlconfigpath={}".format(sqlconfigpath))
                logging.error(err)
                f.close()

        #extract data
        sec="Credentials"
        if config.has_section(sec):
            if config.has_option(sec,  "hostname"):
                dbhost = config.get(sec ,  "hostname")
            elif config.has_option(sec,  "host"):
                dbhost = config.get(sec ,  "host")
            else:
                dbhost = ""
                
            if config.has_option(sec,  "username"):
                dbuser= config.get(sec,  "username")
            elif config.has_option(sec,  "user"):
                dbuser= config.get(sec,  "user")
            else:
                dbuser= ""
                
            if config.has_option(sec,  "password"):
                dbpassword = config.get(sec, "password")
            elif config.has_option(sec,  "pass"):
                dbpassword = config.get(sec, "pass")   
            else:                 
                dbpassword = ""   
                 
            if config.has_option(sec,  "prefix"):
                dbprefix = config.get(sec,  "prefix")
            else:
                dbprefix = ""
        else:
            dbhost = ""
            dbuser = ""
            dbpassword = ""
            dbprefix = ""
            
        self.dbhost = dbhost
        self.dbuser = dbuser
        self.dbpassword = dbpassword
        self.db = dbprefix + self.scriptname
        
        #get config data specific to this bot
#        sec = self.scriptname
#        repliedToTable = "repliedTo"
#        if config.has_section(sec):
#            if config.has_option(sec,  "replytable"):
#                repliedToTable = config.get(sec,  "replytable")     
        
    def DbConnect (self):
        logging.debug("Starting DbConnect().")
        try:
            sqlConn = mysql.connector.connect(user=self.dbuser
                                                                    ,password=self.dbpassword
                                                                    ,host=self.dbhost
                                                                    ,database=self.db)
            return sqlConn
        except mysql.connector.Error as err:
            logging.error("SQL ERROR. Could not connect with user={}    password={}    host={}    database={}".format(self.dbuser, self.dbpassword, self. dbhost, self.db))
            logging.error(err)
            return None
            
    def retrieve (self,  tableName):
        results = []
        #determine connection type
        if self.type == "mysql":
            #Open database connection
            sqlConn = self.DbConnect()
            #retrieve values
            cursor = sqlConn.cursor()
            query = "SELECT id FROM {};".format(tableName)  #should probably sanitize table name for mysql special characters
            logging.debug(query)
            cursor.execute(query)
            for (id) in cursor:
                logging.debug(id[0])
                results.append(id[0])
            cursor.close()
            # Close database connection
            sqlConn.close()
        else:
            logging.error("Somehow this got called with type equal to something other than mysql, even though that code isn't written yet.")
        
        #return list of values
        return results
        
    def store(self,  tableName,  data):
        #determine connection type
        if self.type == "mysql":
            #Open database connection        
            sqlConn = self.DbConnect()
            cursor = sqlConn.cursor()
            d = datetime.datetime.now()
            #store values
            for i in data:
                query = "INSERT INTO {} (id, replydate) VALUES (\'{}\', \'{}\')".format(tableName,  i,  d.strftime('%Y-%m-%d %H:%M:%S'))
                logging.debug(query)
                cursor.execute(query)
                
            logging.debug("Committing")
            sqlConn.commit()
            cursor.close()
            # Close the database connection
            sqlConn.close()
        else:
            logging.error("Somehow this got called with type equal to something other than mysql, even though that code isn't written yet.")
        
