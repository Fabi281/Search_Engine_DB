import pymysql
import sys
from environs import Env
from enum import Enum

from regex import R
env = Env()
env.read_env()

class Database:
    '''
    On Initialization: Establishes a Connection to a MariaDB Database and creates the required Tables if they do not exist.
    This Object formats everything as it needs to be, you just need to pass the data and table-type which is stored in the "Table" Enum.
    You can: Test your connection, insert a single value, insert multiple values and perform any query (single only).
    The Connection is closed at the end of the program or when the object is deleted.
    '''
    conn = ""
    cur = ""

    class Table(Enum):
        word = "word"
        link = "link"
        wordrelation = "wordrelation" 

    def __init__(self):
        try:
            self.conn = pymysql.connect(
                user= env("user"),
                password= env("password"),
                host= env("host"),
                port= int(env("port")),
                database= env("database"),
                autocommit= True
            )
            self.cur = self.conn.cursor()
            
            self.cur.execute("CREATE TABLE IF NOT EXISTS link (id INT NOT NULL AUTO_INCREMENT, url TEXT, language VARCHAR(255) NOT NULL, title TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (id), UNIQUE (url))")
            self.cur.execute("CREATE TABLE IF NOT EXISTS word (id INT NOT NULL AUTO_INCREMENT, word VARCHAR(255) NOT NULL, PRIMARY KEY (id), UNIQUE (word), FULLTEXT (word) WITH PARSER ngram)")
            self.cur.execute("CREATE TABLE IF NOT EXISTS wordrelation (word_id INT NOT NULL, link_id INT NOT NULL, weight INT, PRIMARY KEY (word_id, link_id), FOREIGN KEY (word_id) REFERENCES word(id), FOREIGN KEY (link_id) REFERENCES link(id))")
            self.cur.execute("CREATE TABLE IF NOT EXISTS starturls (id INT NOT NULL AUTO_INCREMENT, url TEXT NOT NULL, PRIMARY KEY (id), UNIQUE (url))")
        except pymysql.OperationalError as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Other error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        
    def __del__(self):
        self.conn.close()

    def delete_word_relation(self, link_id):
        '''Deletes all word relations for a given link_id'''
        self.cur.execute(f"DELETE FROM wordrelation WHERE link_id = {link_id}")
    
    def update_timestamp(self, link_id):
        '''Updates the timestamp of a link'''
        self.cur.execute(f"UPDATE link SET timestamp = CURRENT_TIMESTAMP WHERE id = {link_id}")

    def get_timestamp(self, url):
        '''Returns the timestamp of a link'''
        return self.get_from_query(f"SELECT timestamp FROM link WHERE url = '{url}'")[0][0]
    
    def get_all_start_urls(self):
        '''Returns all start urls'''
        results = self.get_from_query("SELECT url FROM starturls")
        return [result[0] for result in results]
    
    def add_start_url(self, url):
        '''Adds a start url to the starturls table.'''
        self.cur.execute(f"INSERT INTO starturls (url) VALUES ('{url}')")

    def get_from_query(self, query):
        try:
            self.cur.execute(query)
        except pymysql.Error as e:
            print(f"Error executing query: {e}")
        return self.cur.fetchall()

    def insert_single_into_single_table(self, table, value):

        '''Please provide a string of tablename + columnname the value should be added at. Values can also be a list of values with 
        the same pattern.
        Example: insert_single_into_single_table(Database.Table.word.value, ("test",)) => <word>
        Example: insert_single_into_single_table(Database.Table.link.value, ("www.google.com", "German")) => <url>, <language>
        Example: insert_single_into_single_table(Database.Table.wordrelation.value, (1,1,1)) => <word_id>, <link_id>, <weight>
        '''

        id = None
        value += (value[0],)

        # Ich bin aktuell noch auf Python 3.9 deswegen kein Match
        if(table == self.Table.word.value):
            mySql_insert_query = """INSERT INTO word (word) VALUES (%s) ON DUPLICATE KEY UPDATE word = %s"""
        elif(table == self.Table.link.value):
            mySql_insert_query = """INSERT INTO link (url, language, title) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE url = %s"""
        elif(table == self.Table.wordrelation.value):
            mySql_insert_query = """INSERT wordrelation (word_id, link_id, weight) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE word_id = %s"""

        try:
            self.cur.execute(mySql_insert_query, value)
        except pymysql.Error as e:
                print(f"Error: {e}")

        if(table == self.Table.word.value):
            id = self.get_from_query(f'SELECT id FROM word WHERE word = "{self.conn.escape_string(value[0])}"')
        elif(table == self.Table.link.value):
            id = self.get_from_query(f'SELECT id FROM link WHERE link.url = "{self.conn.escape_string(value[0])}" AND link.language = "{self.conn.escape_string(value[1])}"')
        elif(table == self.Table.wordrelation.value):
            id = self.get_from_query(f'SELECT word_id, link_id FROM wordrelation WHERE wordrelation.word_id = {value[0]} AND wordrelation.link_id = {value[1]} AND wordrelation.weight = {value[2]}')

        return id
    
    def insert_multiple_into_single_table(self, table, values):

        '''Please provide a string of tablename + columnname the value should be added at. Values can also be a list of values with 
        the same pattern.
        Example: insert_multiple_into_single_table(Database.Table.word.value, [("wordTuple1",), ("wordTuple2",)]) => <word>
                 insert_multiple_into_single_table(Database.Table.link.value, [("www.stackoverflow.com/", "German"), ("www.youtube.com", "English")]) => ("<url>", "<language>")])
                 insert_multiple_into_single_table(Database.Table.wordrelation.value, [(1, 1, 1), (2, 2, 2)]) => (<word_id>, <link_id>, <weight>)   
        '''

        id = None
        #Append first value for update query so it can be used in the loop and duplicates are ignored
        values_with_duplicate_protection = [value + (value[0],) for value in values]

        if(table == self.Table.word.value):
            mySql_insert_query = """INSERT INTO word (word) VALUES (%s) ON DUPLICATE KEY UPDATE word = %s"""
        elif(table == self.Table.link.value):
            mySql_insert_query = """INSERT INTO link (url, language, title) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE url = %s"""
        elif(table == self.Table.wordrelation.value):
            mySql_insert_query = """INSERT INTO wordrelation (word_id, link_id, weight) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE word_id = %s"""

        try:
            #self.cur.executemany(mySql_insert_query, values_with_duplicate_protection)
            for value in values_with_duplicate_protection:
                self.cur.execute(mySql_insert_query, value)
        except pymysql.Error as e:
                print(f"Error: {e}")
        
        if(table == self.Table.word.value):
            valuelist = ', '.join([
                f'"{self.conn.escape_string(w[0])}"' for w in values])

            id = self.get_from_query(f"SELECT id FROM word WHERE word.word IN ({valuelist}) ORDER BY FIELD(word.word,{valuelist})")
        elif(table == self.Table.link.value):
            valuelist_url = ', '.join([f'"{self.conn.escape_string(w[0])}"' for w in values])
            valuelist_language = ', '.join([f'"{self.conn.escape_string(w[1])}"' for w in values])

            id = self.get_from_query(f"SELECT id FROM link WHERE link.url IN ({valuelist_url}) AND link.language IN ({valuelist_language}) ORDER BY FIELD(link.url,{valuelist_url})")
        elif(table == self.Table.wordrelation.value):
            valuelist_word_id = ', '.join([f'"{w[0]}"' for w in values])
            valuelist_link_id = ', '.join([f'"{w[1]}"' for w in values])
            valuelist_weight = ', '.join([f'"{w[2]}"' for w in values])

            id = self.get_from_query(f"SELECT word_id, link_id FROM wordrelation WHERE word_id IN ({valuelist_word_id}) AND wordrelation.link_id IN ({valuelist_link_id}) AND  wordrelation.weight IN ({valuelist_weight})")
        
        return id

    def get_all_languages(self):
        '''Returns a list of all languages'''
        return self.get_from_query("SELECT DISTINCT language FROM link")
    
    def test_my_connection(self):
        '''
        Test your connection to the MariaDB Database by executing a simple query (Fetch all words).
        '''
        try:
            self.cur.execute("SELECT * FROM word")
        except pymysql.Error as e:
            print(f"Error: {e}")
            return False
        return self.cur.fetchall()
