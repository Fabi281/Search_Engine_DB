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
    The Connection is closed at the end of the program or when the object is deleted.
    '''
    conn = ""
    cur = ""

    class Table(Enum):
        word = "word"
        link = "link"
        wordrelation = "wordrelation"
        starturls = "starturls"
        alloweddomains = "alloweddomains"
        backlinks = "backlinks"

    def __init__(self):
        try:
            self.conn = pymysql.connect(
                user=env("MYSQL_USER"),
                password=env("MYSQL_PASSWORD"),
                host=env("host"),
                port=int(env("port")),
                database=env("MYSQL_DATABASE"),
                autocommit=True
            )
            self.cur = self.conn.cursor()

            self.cur.execute("CREATE TABLE IF NOT EXISTS link (id INT NOT NULL AUTO_INCREMENT, url VARCHAR(255), language VARCHAR(255) NOT NULL, title TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY (id), UNIQUE (url))")
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS word (id INT NOT NULL AUTO_INCREMENT, word VARCHAR(255) NOT NULL, PRIMARY KEY (id), UNIQUE (word), FULLTEXT (word) WITH PARSER ngram)")
            self.cur.execute("CREATE TABLE IF NOT EXISTS wordrelation (word_id INT NOT NULL, link_id INT NOT NULL, weight INT, PRIMARY KEY (word_id, link_id), FOREIGN KEY (word_id) REFERENCES word(id), FOREIGN KEY (link_id) REFERENCES link(id))")
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS starturls (id INT NOT NULL AUTO_INCREMENT, url VARCHAR(255) NOT NULL, PRIMARY KEY (id), UNIQUE (url))")
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS alloweddomains (id INT NOT NULL AUTO_INCREMENT, domain VARCHAR(255) NOT NULL, PRIMARY KEY (id), UNIQUE (domain))")
            self.cur.execute(
                "CREATE TABLE IF NOT EXISTS backlinks (link_id_from INT NOT NULL, url_to VARCHAR(255) NOT NULL, PRIMARY KEY (link_id_from, url_to), FOREIGN KEY (link_id_from) REFERENCES link(id), INDEX (url_to))")
        except pymysql.OperationalError as e:
            print(f"Error connecting to Database Platform: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Other error connecting to Database Platform: {e}")
            sys.exit(1)

    def __del__(self):
        self.conn.close()

    def get_timestamp(self, url):
        '''Returns the timestamp of a link'''
        result = self.get_from_query(
            f"SELECT timestamp FROM link WHERE url = '{url}'")
        if len(result):
            return result[0][0]
        return None

    def get_all_start_urls(self):
        '''Returns all start urls and ids'''
        results = self.get_from_query("SELECT id, url FROM starturls")
        return [{"id": result[0], "url": result[1]} for result in results]

    def get_all_allowed_domains(self):
        '''Returns a list of all allowed domains and ids'''
        results = self.get_from_query("SELECT id, domain FROM alloweddomains")
        return [{"id": result[0], "domain": result[1]} for result in results]

    def get_all_languages(self):
        '''Returns a list of all languages and ids'''
        results = self.get_from_query("SELECT id, language FROM link")
        return [{"id": result[0], "language": result[1]} for result in results]

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
        Example: insert_single_into_single_table(Database.Table.starturls.value, ("https://www.google.com",)) => <starturl>
        Example: insert_single_into_single_table(Database.Table.alloweddomains.value, ("www.google.com",)) => <alloweddomain>
        Example: insert_single_into_single_table(Database.Table.backlinks.value, (1,"www.google.com")) => <link_id_from>, <url_to>
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
        elif(table == self.Table.starturls.value):
            mySql_insert_query = """INSERT INTO starturls (url) VALUES (%s) ON DUPLICATE KEY UPDATE url = %s"""
        elif(table == self.Table.alloweddomains.value):
            mySql_insert_query = """INSERT INTO alloweddomains (domain) VALUES (%s) ON DUPLICATE KEY UPDATE domain = %s"""
        elif(table == self.Table.backlinks.value):
            mySql_insert_query = """INSERT INTO backlinks (link_id_from, url_to) VALUES (%s, %s) ON DUPLICATE KEY UPDATE link_id_from = %s"""

        try:
            self.cur.execute(mySql_insert_query, value)
        except pymysql.Error as e:
            print(f"Error: {e}")

        if(table == self.Table.word.value):
            id = self.get_from_query(
                f'SELECT id FROM word WHERE word = "{self.conn.escape_string(value[0])}"')
        elif(table == self.Table.link.value):
            id = self.get_from_query(
                f'SELECT id FROM link WHERE link.url = "{self.conn.escape_string(value[0])}" AND link.language = "{self.conn.escape_string(value[1])}"')
        elif(table == self.Table.wordrelation.value):
            id = self.get_from_query(
                f'SELECT word_id, link_id FROM wordrelation WHERE wordrelation.word_id = {value[0]} AND wordrelation.link_id = {value[1]} AND wordrelation.weight = {value[2]}')
        elif(table == self.Table.starturls.value):
            id = self.get_from_query(
                f'SELECT id FROM starturls WHERE starturls.url = "{self.conn.escape_string(value[0])}"')
        elif(table == self.Table.alloweddomains.value):
            id = self.get_from_query(
                f'SELECT id FROM alloweddomains WHERE alloweddomains.domain = "{self.conn.escape_string(value[0])}"')
        elif(table == self.Table.backlinks.value):
            id = self.get_from_query(
                f'SELECT link_id_from, url_to FROM backlinks WHERE backlinks.link_id_from = {value[0]} AND backlinks.url_to = "{self.conn.escape_string(value[1])}"')

        return id

    def insert_multiple_into_single_table(self, table, values):
        '''Please provide a string of tablename + columnname the value should be added at. Values can also be a list of values with 
        the same pattern.
        Example: insert_multiple_into_single_table(Database.Table.word.value, [("wordTuple1",), ("wordTuple2",)]) => <word>
                 insert_multiple_into_single_table(Database.Table.link.value, [("www.stackoverflow.com/", "German"), ("www.youtube.com", "English")]) => ("<url>", "<language>")])
                 insert_multiple_into_single_table(Database.Table.wordrelation.value, [(1, 1, 1), (2, 2, 2)]) => (<word_id>, <link_id>, <weight>)
                 insert_multiple_into_single_table(Database.Table.starturls.value, [("https://www.stackoverflow.com",), ("https://www.youtube.com",)]) => <starturl>   
                 insert_multiple_into_single_table(Database.Table.alloweddomains.value, [("www.stackoverflow.com",), ("www.youtube.com",)]) => <alloweddoamain>   
                 insert_multiple_into_single_table(Database.Table.backlink.value, [(1, "www.stackoverflow.com"), (2, "www.youtube.com")]) => (<link_id_from>, <url_to>)
        '''

        id = None

        if(table == self.Table.word.value):
            mySql_insert_query = """INSERT IGNORE INTO word (word) VALUES (%s) """
        elif(table == self.Table.link.value):
            mySql_insert_query = """INSERT IGNORE INTO link (url, language, title) VALUES (%s, %s, %s)"""
        elif(table == self.Table.wordrelation.value):
            mySql_insert_query = """INSERT IGNORE INTO wordrelation (word_id, link_id, weight) VALUES (%s, %s, %s)"""
        elif(table == self.Table.starturls.value):
            mySql_insert_query = """INSERT IGNORE INTO starturls (url) VALUES (%s)"""
        elif(table == self.Table.alloweddomains.value):
            mySql_insert_query = """INSERT IGNORE INTO alloweddomains (domain) VALUES (%s)"""
        elif(table == self.Table.backlinks.value):
            mySql_insert_query = """INSERT IGNORE INTO backlinks (link_id_from, url_to) VALUES (%s, %s)"""

        try:
            self.cur.executemany(mySql_insert_query, values)
        except pymysql.Error as e:
            print(f"Error: {e}")

        if(table == self.Table.word.value):
            valuelist = ', '.join([
                f'"{self.conn.escape_string(w[0])}"' for w in values])
            id = self.get_from_query(
                f"SELECT id FROM word WHERE word.word IN ({valuelist}) ORDER BY FIELD(word.word,{valuelist})")
        elif(table == self.Table.link.value):
            valuelist_url = ', '.join(
                [f'"{self.conn.escape_string(w[0])}"' for w in values])
            valuelist_language = ', '.join(
                [f'"{self.conn.escape_string(w[1])}"' for w in values])

            id = self.get_from_query(
                f"SELECT id FROM link WHERE link.url IN ({valuelist_url}) AND link.language IN ({valuelist_language}) ORDER BY FIELD(link.url,{valuelist_url})")
        elif(table == self.Table.wordrelation.value):
            valuelist_word_id = ', '.join([f'"{w[0]}"' for w in values])
            valuelist_link_id = ', '.join([f'"{w[1]}"' for w in values])
            valuelist_weight = ', '.join([f'"{w[2]}"' for w in values])

            id = self.get_from_query(
                f"SELECT word_id, link_id FROM wordrelation WHERE word_id IN ({valuelist_word_id}) AND wordrelation.link_id IN ({valuelist_link_id}) AND  wordrelation.weight IN ({valuelist_weight})")
        elif(table == self.Table.starturls.value):
            valuelist = ', '.join([
                f'"{self.conn.escape_string(w[0])}"' for w in values])
            id = self.get_from_query(
                f"SELECT id FROM starturls WHERE starturls.url IN ({valuelist}) ORDER BY FIELD(starturls.url,{valuelist})")
        elif(table == self.Table.alloweddomains.value):
            valuelist = ', '.join([
                f'"{self.conn.escape_string(w[0])}"' for w in values])
            id = self.get_from_query(
                f"SELECT id FROM alloweddomains WHERE alloweddomains.domain IN ({valuelist}) ORDER BY FIELD(alloweddomains.domain,{valuelist})")
        elif(table == self.Table.backlinks.value):
            valuelist_link_id_from = ', '.join([f'"{w[0]}"' for w in values])
            valuelist_url_to = ', '.join([
                f'"{self.conn.escape_string(w[1])}"' for w in values])

            id = self.get_from_query(
                f"SELECT link_id_from, url_to FROM backlinks WHERE backlinks.link_id_from IN ({valuelist_link_id_from}) AND backlinks.url_to IN ({valuelist_url_to})")

        return id

    def update_timestamp(self, link_id):
        '''Updates the timestamp of a link'''
        self.cur.execute(
            f"UPDATE link SET timestamp = CURRENT_TIMESTAMP WHERE id = {link_id}")

    def delete_from_table(self, table, id):
        '''
        Deletes a row from a table.
        Example: delete_from_table(Database.Table.word.value, 1) => deletes the word with id 1
                delete_from_table(Database.Table.wordrelation.value, [1,2]) => deletes the wordrelation with link_id 1 and word_id 2
        '''
        if(table == Database.Table.wordrelation.value):
            self.cur.execute(
                f"DELETE FROM wordrelation WHERE link_id = {id[0]} AND word_id = {id[1]}")
        elif(table == Database.Table.backlinks.value):
            self.cur.execute(
                f'DELETE FROM backlinks WHERE link_id_from = {id[0]} AND url_to = "{self.conn.escape_string(id[1])}"')
        else:
            self.cur.execute(f"DELETE FROM {table} WHERE id = {id}")

    def search_db_with_query(self, query, language, weight_tfidf=0.6, weight_match=0.2, weight_backlink=0.2, page=1, limit=10):
        '''Returns a list of all links that contain the search query'''
        results = self.get_from_query(f"""
            WITH max_backlinks AS (
                SELECT MAX(count.count)
                from (
                    SELECT
                        COUNT(*) as count
                    from
                        backlinks
                    GROUP BY
                        backlinks.url_to
                ) as count
            ),
            selected_word_relations AS (
            SELECT
                wordrelation.link_id,
                wordrelation.weight,
                link.url,
                link.title
            FROM
                wordrelation
                JOIN word on word.id = wordrelation.word_id
                JOIN link on link.id = wordrelation.link_id
            WHERE
                MATCH (word.word) AGAINST ('{self.conn.escape_string(query)}' in boolean mode)
                AND link.language = '{self.conn.escape_string(language)}'
            ),
            backlinks AS (
                SELECT
                COUNT(DISTINCT backlinks.link_id_from) AS count,
                selected_word_relations.link_id
                from
                backlinks
                join selected_word_relations on selected_word_relations.url = backlinks.url_to
                GROUP BY
                backlinks.url_to
            )
            SELECT
            selected_word_relations.weight / (
                SELECT
                SUM(weight)
                from
                wordrelation
                WHERE
                wordrelation.link_id = selected_word_relations.link_id
            ) * LOG(
                (
                SELECT
                    COUNT(*)
                from
                    wordrelation
                ) / (
                SELECT
                    COUNT(DISTINCT selected_word_relations.link_id)
                from
                    selected_word_relations
                )
            ) * {weight_tfidf} + {1-weight_tfidf} * LOG((
                SELECT
                   count
                FROM 
                    backlinks
                WHERE 
                    backlinks.link_id = selected_word_relations.link_id 
            )) / LOG((
                SELECT * from max_backlinks
            )) as ranking,
            selected_word_relations.url,
            selected_word_relations.title
            from
            selected_word_relations
            order by
            ranking desc
        limit {limit} offset {(page - 1) * limit};
        """)
        return [{'url': result[1], 'rank': result[0], 'title': result[2]} for result in results]

    def predict_words_for_query(self, query):
        words = query.split(' ')
        # predict_word for each word 
        res = [self.predict_word(word) for word in words]
        # flatten
        res = [word for word_list in res for word in word_list]
        return res

    def predict_word(self, word):
        results = self.get_from_query(f"""
        SELECT
            word
        from
            word
        where
            MATCH (word) AGAINST ('{self.conn.escape_string(word)}' in boolean mode)
        LIMIT 6;
        """)
        return [result[0] for result in results]

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
