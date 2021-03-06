# Search_Engine_DB
This is a small project to recreate a small scale search engine using python.

We scrape each website in a starturl database for links to other websites. And
recursivly search them aswell. The scraping process is limited to allowed Domains which are stored in
another database which can all be customized inside a streamlit website.

The Project is structured as follows:
1. DB => This contains the Connection, Disconnection, Creation of Tables and all Interfaces for Reads, Writes and Updates aswell as Constraints and  the necessary formatting
2. Scraper => This contains the scraper, which uses the DB Interface to write and read the results in the Database. We used language recognition, lemmatization, Stop-Word-Elimination,ngram-parsing, TFIDF Document Ranking and Backlinking to improve the search results.
3. Website => This contains a frontend with admin and user sites. The user site is the search engine itself which allows search for words and part of words. It returns a certain number of the most relevant websites based on the scraper Results


# Databasse Structure
We use MySQL with the following structure:
![Here could be your picture](ER-Diagram.PNG)
This is a simplified Version of our Database structure. If you want
to know everything (like constraints and automatic updates) please refer to the code of the constructor in "DB/Database.py".

# Run the Application
You can deploy this application with the following steps:

1. Create a .env in the "DB"-Folder with the following scheme:

| Key      | Value |
| ----------- | ----------- |
| MYSQL_USER      | "Username"       |
| MYSQL_PASSWORD   | "Password"        |
| host      | "database" (Required to be this Value!)      |
| port   | 3306 (Required to be this Value!)         |
| MYSQL_DATABASE      | "Databasename"       |

2. Run Docker Compose ( docker compose -f "docker-compose-db.yaml" up -d --build ) on the docker-compose-db.yaml, this creates the mysql-database and a phpmyadmin interface (Note: Sometimes it takes a while after starting to initialize the database. If you get an Error when trying to access it via PHPMyAdmin just give it a minute or two and try again)
3. ONLY CONTINUE IF THE PREVIOUS STEP IS DONE (AND IF THERE IS THE DATABSE IN PHPMYADMIN). Run Docker Compose ( docker compose -f "docker-compose-spider.yaml" up -d --build ) on the docker-compose-spider.yaml to run the scraper which fills the database
4. Run Docker Compose ( docker compose -f "docker-compose-website.yaml" up -d --build ) on the docker-compose-website.yaml to run the frontend with admin and user interface
