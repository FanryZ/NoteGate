import sqlite3
import os
from .page import Page

if not os.path.exists('./database'):
    os.makedirs('./database')
conn = sqlite3.connect('./database/notegate.db')
c = conn.cursor()

def note_num():
    res = c.execute("select ID from NOTE")
    return len(res.fetchall())

def insert(page: Page, tokens: str, pro: bool):
    key_id = note_num()
    excerpt = page.excerpt if page.excerpt else ""
    command = '''INSERT INTO NOTE (ID, WEBID, TITLE, EXCERPT, TOKEN, AUTHOR, AUTHORID, PRO) VALUES
                            ({}, '{}', '{}', '{}', '{}', '{}', '{}', {})
        '''.format(key_id, page.web_id, page.title, excerpt, tokens, page.user_name, page.user_id, pro)
    print(command)
    c.execute(
        command
    )

def get_token_pro():
    res = c.execute("select TOKEN, PRO from NOTE")
    pairs = res.fetchall()
    return pairs

def print_all():
    res = c.execute("select ID, TITLE, TOKEN, PRO from NOTE")
    notes = res.fetchall()
    for id, title, tokens, pro in notes:
        print("{}, {}, {}, {}".format(id, title, tokens, pro))

# if __name__ == "__main__":
tables = c.execute("select name from sqlite_master")
table_names = [table[0] for table in tables.fetchall()]
if "NOTE" not in table_names:
    c.execute('''CREATE TABLE NOTE
                    (ID INT PRIMARY KEY     NOT NULL,
                    WEBID           CHAR(50) NOT NULL,
                    TITLE           TEXT    NOT NULL,
                    EXCERPT         TEXT,
                    TOKEN           INT     NOT NULL,
                    AUTHOR          TEXT,
                    AUTHORID        CHAR(50),
                    PRO             BOOL    NOT NULL
            )
            ;''')
