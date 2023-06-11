import os
import sqlite3 as sqlite
from typing import List
import random
import base64
import simplejson as json
from be.model.db_conn import DBConn
from sqlalchemy import Column, String, create_engine, Integer, Text, Date, LargeBinary
from be.model.store import get_db_conn, get_db_base

Base = get_db_base()

class books(Base):
    __tablename__ = 'book'

    id = Column(Text, primary_key=True, unique=True, nullable=False)
    title = Column(Text)
    author = Column(Text)
    publisher = Column(Text)
    original_title = Column(Text)
    translator = Column(Text)
    pub_year = Column(Text)
    pages = Column(Integer)
    price = Column(Integer)
    currency_unit = Column(Text)
    binding = Column(Text)
    isbn = Column(Text)
    author_intro = Column(Text)
    book_intro = Column(Text)
    content = Column(Text)
    tags = Column(Text)
    picture = Column(LargeBinary)

    def to_dict(self):
        result = {}
        result['id'] = self.id
        result['title'] = self.title
        result['author'] = self.author
        result['publisher'] = self.publisher
        result['original_title'] = self.original_title
        result['translator'] = self.translator
        result['pub_year'] = self.pub_year
        result['pages'] = self.pages
        result['price'] = self.price
        result['currency_unit'] = self.currency_unit
        result['binding'] = self.binding
        result['isbn'] = self.isbn
        result['author_intro'] = self.author_intro
        result['book_intro'] = self.book_intro
        result['content'] = self.content
        result['tags'] = self.tags
        result['picture'] = self.picture
        return result

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: List[str]
    pictures: List[bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
        self.session = get_db_conn()


    def get_book_count(self):

        return len(self.session.query(books).all())

    def get_book_info(self, start, size) -> List[Book]:
        bookres = []

        result = self.session.query(books).order_by(books.id).offset(start).limit(size).all()
        for row in result:
            book = Book()
            book.id = row.id
            book.title = row.title
            book.author = row.author
            book.publisher = row.publisher
            book.original_title = row.original_title
            book.translator = row.translator
            book.pub_year = row.pub_year
            book.pages = row.pages
            book.price = row.price

            book.currency_unit = row.currency_unit
            book.binding = row.binding
            book.isbn = row.isbn
            book.author_intro = row.author_intro
            book.book_intro = row.book_intro
            book.content = row.content
            tags = row.tags
            picture = row.picture

            for tag in tags.split("\n"):
                if tag.strip() != "":
                    book.tags.append(tag)
            for i in range(0, random.randint(0, 9)):
                if picture is not None:
                    encode_str = base64.b64encode(picture).decode('utf-8')
                    book.pictures.append(encode_str)
            bookres.append(book)


        return bookres