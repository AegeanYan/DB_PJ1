import sqlite3 as sqlite

from sqlalchemy_utils import drop_database, create_database
from be.model.store import init_database, get_db_conn
from fe.access.book import books

drop_database('postgresql://postgres:0518@127.0.0.1:5432/bookstore')

create_database('postgresql://postgres:0518@127.0.0.1:5432/bookstore')

init_database()
session = get_db_conn()

conn = sqlite.connect('fe/data/book.db')
cursor = conn.execute(
    "SELECT id, title, author, "
    "publisher, original_title, "
    "translator, pub_year, pages, "
    "price, currency_unit, binding, "
    "isbn, author_intro, book_intro, "
    "content, tags, picture FROM book ORDER BY id "
)
for row in cursor:
    new_book = books(
    	id = row[0],
    	title = row[1],
    	author = row[2],
    	publisher = row[3],
    	original_title = row[4],
    	translator = row[5],
    	pub_year = row[6],
    	pages = row[7],
    	price = row[8],

    	currency_unit = row[9],
    	binding = row[10],
    	isbn = row[11],
    	author_intro = row[12],
    	book_intro = row[13],
    	content = row[14],
    	tags = row[15],
    	picture = row[16]
	)
    session.add(new_book)
    session.commit()

session.close()
cursor.close()
conn.close()