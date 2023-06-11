import logging
import os
import sqlite3 as sqlite
import datetime
import sqlalchemy
from sqlalchemy import Column, String, create_engine, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import time


class Store():
    def __init__(self):
        self.engine = create_engine('postgresql://postgres:0518@127.0.0.1:5432/bookstore',
            echo = False,
            pool_size = 8,
            pool_recycle = 60 * 30
        )
        self.ss_mkr = sessionmaker(bind=self.engine)
        self.session = self.ss_mkr()
        self.Base = sqlalchemy.orm.declarative_base()

    def get_db_conn(self):
        return self.session

database_instance: Store = Store()

Base = database_instance.Base

def init_database():
    global database_instance
    database_instance.Base.metadata.create_all(database_instance.engine)

def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()

def get_db_base():
    global database_instance
    return database_instance.Base

class users(Base):
    __tablename__ = 'user'

    user_id = Column(Text, primary_key=True, unique=True, nullable=False, index=True)
    password = Column(Text, nullable=False)
    balance = Column(Integer, nullable=False)
    token = Column(Text)
    terminal = Column(Text)

class user_store(Base):
    __tablename__ = 'user_store'

    user_id = Column(Text, primary_key=True, nullable=False, index=True)
    store_id = Column(Text, primary_key=True,  nullable=False, index=True)

class stores(Base):
    __tablename__ = 'store'
    
    store_id = Column(Text, primary_key=True, nullable=False, index=True)
    book_id = Column(Text, primary_key=True, nullable=False, index=True)
    book_info = Column(Text)
    stock_level = Column(Integer, nullable=False)

class new_order(Base):
    __tablename__ = 'new_order'

    order_id = Column(Text, primary_key=True, unique=True, nullable=False, index=True)
    user_id = Column(Text, nullable=False)
    store_id = Column(Text, nullable=False)
    status = Column(Integer, nullable=False)
    create_time = Column(DateTime, nullable=False)
    total_price = Column(Integer, nullable=False)

    def to_dict(self):
        result = {}
        result['order_id'] = self.order_id
        result['user_id'] = self.user_id
        result['store_id'] = self.store_id
        result['status'] = self.status
        result['create_time'] = self.create_time
        result['total_price'] = self.total_price
        return result

class new_order_detail(Base):
    __tablename__ = 'new_order_detail'

    order_id = Column(Text, primary_key=True, nullable=False, index=True)
    book_id = Column(Text, primary_key=True, nullable=False, index=True)
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    def to_dict(self):
        result = {}
        result['order_id'] = self.order_id
        result['book_id'] = self.book_id
        result['count'] = self.count
        result['price'] = self.price
        return result

