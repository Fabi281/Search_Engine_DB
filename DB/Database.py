import mariadb
import sys
from environs import Env
from enum import Enum
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
            self.conn = mariadb.connect(
                user= env("user"),
                password= env("password"),
                host= env("host"),
                port= int(env("port")),
                database= env("database")
            )
            self.cur = self.conn.cursor()
            
            self.cur.execute("CREATE TABLE IF NOT EXISTS link (id INT NOT NULL AUTO_INCREMENT, url VARCHAR(255) NOT NULL, wordrelation_id INT NOT NULL, PRIMARY KEY (id))")
            self.cur.execute("CREATE TABLE IF NOT EXISTS word (id INT NOT NULL AUTO_INCREMENT, word VARCHAR(255) NOT NULL, PRIMARY KEY (id))")
            self.cur.execute("CREATE TABLE IF NOT EXISTS wordrelation (word_id INT NOT NULL, link_id INT NOT NULL, weight INT, PRIMARY KEY (word_id, link_id), FOREIGN KEY (word_id) REFERENCES word(id), FOREIGN KEY (link_id) REFERENCES link(id))")
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)
        
    def __del__(self):
        self.conn.close()
    
    def get_from_query(self, query):
        try:
            self.cur.execute(query)
        except mariadb.Error as e:
            print(f"Error executing query: {e}")
        return self.cur.fetchall()

    def insert_single_into_single_table(self, table, values):

        '''Please provide a string of tablename + columnname the value should be added at. Values can also be a list of values with 
        the same pattern.
        Example: insert_into_single_table(Database.Table.word.value, "'test'") <word>
        Example: insert_into_single_table(Database.Table.link.value, "'www.heidenheim.dhbw.de/', 1") <url>, <wordrelation_id>
        Example: insert_into_single_table(Database.Table.wordrelation.value, 1, 1, 1") <word_id>, <link_id>, <weight>
        '''
        if(table == self.Table.word.value):
            mySql_insert_query = f"INSERT INTO {table} VALUES ({values})"
        elif(table == self.Table.link.value):
            mySql_insert_query = f"INSERT INTO {table} VALUES ({values})"
        elif(table == self.Table.wordrelation.value):
            mySql_insert_query = f"INSERT INTO {table} VALUES ({values})"
        try:
            self.cur.execute(mySql_insert_query, values)
            self.conn.commit()
        except mariadb.Error as e:
                print(f"Error: {e}")
    
    def insert_multiple_into_single_table(self, table, values):

        '''Please provide a string of tablename + columnname the value should be added at. Values can also be a list of values with 
        the same pattern.
        Example: insert_multiple_into_single_table(Database.Table.word.value, [("wordTuple1",), ("<word>",)])  - IMPORTANT the comma afterwards is needed
                 insert_multiple_into_single_table(Database.Table.link.value, [("'https://stackoverflow.com/'", 1), ("'<url>'", <wordrelation_id>)])
                 insert_multiple_into_single_table(Database.Table.wordrelation.value, [(1, 1, 1), (<word_id>, <link_id>, <weight>)])   
        '''

        if(table == self.Table.word.value):
            mySql_insert_query = """INSERT INTO word (word) VALUES (%s)"""
        elif(table == self.Table.link.value):
            mySql_insert_query = """INSERT INTO link (url, wordrelation_id) VALUES (%s, %s)"""
        elif(table == self.Table.wordrelation.value):
            mySql_insert_query = """INSERT INTO wordrelation (word_id, link_id, weight) VALUES (%s, %s, %s)"""

        try:
            self.cur.executemany(mySql_insert_query, values)
            self.conn.commit()
        except mariadb.Error as e:
                print(f"Error: {e}")
    
    def test_my_connection(self):
        '''
        Test your connection to the MariaDB Database by executing a simple query (Fetch all words).
        '''
        try:
            self.cur.execute("SELECT * FROM word")
        except mariadb.Error as e:
            print(f"Error: {e}")
            return False
        return self.cur.fetchall()