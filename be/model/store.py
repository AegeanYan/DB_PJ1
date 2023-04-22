import logging
import os
import sqlite3 as sqlite
import pymongo


class Store:
    database: str

    def __init__(self, db_path):
        self.database = os.path.join(db_path, "be.db")

        self.client = pymongo.MongoClient("mongodb://localhost:27017/")

        # self.client.drop_database('bookstore')
        self.db = self.client['bookstore']
        self.db['user'].delete_many({})
        self.db['user_store'].delete_many({})
        self.db['store'].delete_many({})
        self.db['new_order'].delete_many({})
        self.db['new_order_detail'].delete_many({})
        
        self.init_tables_mongo()

    # def init_tables(self):
    #     try:
    #         conn = self.get_db_conn()
    #         conn.execute(
    #             "CREATE TABLE IF NOT EXISTS user ("
    #             "user_id TEXT PRIMARY KEY, password TEXT NOT NULL, "
    #             "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
    #         )

    #         conn.execute(
    #             "CREATE TABLE IF NOT EXISTS user_store("
    #             "user_id TEXT, store_id, PRIMARY KEY(user_id, store_id));"
    #         )

    #         conn.execute(
    #             "CREATE TABLE IF NOT EXISTS store( "
    #             "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER,"
    #             " PRIMARY KEY(store_id, book_id))"
    #         )

    #         conn.execute(
    #             "CREATE TABLE IF NOT EXISTS new_order( "
    #             "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT)"
    #         )

    #         conn.execute(
    #             "CREATE TABLE IF NOT EXISTS new_order_detail( "
    #             "order_id TEXT, book_id TEXT, count INTEGER, price INTEGER,  "
    #             "PRIMARY KEY(order_id, book_id))"
    #         )

    #         conn.commit()
    #     except sqlite.Error as e:
    #         logging.error(e)
    #         conn.rollback()

    def init_tables_mongo(self):
        try:
            user_col = self.db['user']
            user_col.create_index([("user_id", 1)], unique=True)

            user_store_col = self.db['user_store']
            user_store_col.create_index([("user_id", 1), ("store_id", 1)], unique=True)

            store_col = self.db['store']
            store_col.create_index([("store_id", 1), ("book_id", 1)], unique=True)
            store_col.create_index([("book_id", 1)])

            new_order_col = self.db['new_order']
            new_order_col.create_index([("order_id", 1)], unique=True)

            new_order_detail_col = self.db['new_order_detail']
            new_order_detail_col.create_index([("order_id", 1), ("book_id", 1)], unique=True)

        except pymongo.errors.PyMongoError as e:
            logging.error(e)

    # def get_db_conn(self) -> sqlite.Connection:
    #     return sqlite.connect(self.database)

    def get_db_mongo(self):
        return self.db


database_instance: Store = None


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


# def get_db_conn():
#     global database_instance
#     return database_instance.get_db_conn()

def get_db_mongo():
    global database_instance
    return database_instance.get_db_mongo()