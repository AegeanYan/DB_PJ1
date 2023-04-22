import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
import pymongo
import datetime
from be.model.user import User
import numpy as np

class Buyer(db_conn.DBConn):
    def __init__(self, limit = np.inf):
        db_conn.DBConn.__init__(self)
        # self.duration_limit = limit
        self.duration_limit = 10

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            for book_id, count in id_and_count:
                result = self.db['store'].find_one({'store_id': store_id, 'book_id': book_id}, {'book_id':1, 'stock_level':1, 'book_info':1})
                if result is None:
                    return error.error_non_exist_book_id(book_id) + (order_id, )

                stock_level = result['stock_level']
                book_info = result['book_info']
                book_info_json = json.loads(book_info)
                price = book_info_json['price']

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                result = self.db['store'].update_many({'store_id': store_id, 'book_id': book_id, 'stock_level': {'$gte': count}}, {'$inc': {'stock_level': -count}})
                if result.matched_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )

                order_detail = {
                    "order_id" : uid,
                    "book_id" : book_id,
                    "count" : count,
                    "price" : price
                }
                self.db['new_order_detail'].insert_one(order_detail)

            order = {
                "order_id" : uid,
                "store_id" : store_id,
                "user_id" : user_id,
                "status" : 0,
                "create_time" : datetime.datetime.now()
            }
            self.db['new_order'].insert_one(order)
            order_id = uid
        except pymongo.errors.PyMongoError as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    # def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
    #     order_id = ""
    #     try:
    #         if not self.user_id_exist(user_id):
    #             return error.error_non_exist_user_id(user_id) + (order_id, )
    #         if not self.store_id_exist(store_id):
    #             return error.error_non_exist_store_id(store_id) + (order_id, )
    #         uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

    #         for book_id, count in id_and_count:
    #             cursor = self.conn.execute(
    #                 "SELECT book_id, stock_level, book_info FROM store "
    #                 "WHERE store_id = ? AND book_id = ?;",
    #                 (store_id, book_id))
    #             row = cursor.fetchone()
    #             if row is None:
    #                 return error.error_non_exist_book_id(book_id) + (order_id, )

    #             stock_level = row[1]
    #             book_info = row[2]
    #             book_info_json = json.loads(book_info)
    #             price = book_info_json.get("price")

    #             if stock_level < count:
    #                 return error.error_stock_level_low(book_id) + (order_id,)

    #             cursor = self.conn.execute(
    #                 "UPDATE store set stock_level = stock_level - ? "
    #                 "WHERE store_id = ? and book_id = ? and stock_level >= ?; ",
    #                 (count, store_id, book_id, count))
    #             if cursor.rowcount == 0:
    #                 return error.error_stock_level_low(book_id) + (order_id, )

    #             self.conn.execute(
    #                     "INSERT INTO new_order_detail(order_id, book_id, count, price) "
    #                     "VALUES(?, ?, ?, ?);",
    #                     (uid, book_id, count, price))

    #         self.conn.execute(
    #             "INSERT INTO new_order(order_id, store_id, user_id) "
    #             "VALUES(?, ?, ?);",
    #             (uid, store_id, user_id))
    #         self.conn.commit()
    #         order_id = uid
    #     except sqlite.Error as e:
    #         logging.info("528, {}".format(str(e)))
    #         return 528, "{}".format(str(e)), ""
    #     except BaseException as e:
    #         logging.info("530, {}".format(str(e)))
    #         return 530, "{}".format(str(e)), ""

    #     return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            result = self.db['new_order'].find_one({'order_id': order_id}, {'order_id':1, 'user_id':1, 'store_id':1, 'status':1, 'create_time':1})
            if result is None:
                return error.error_invalid_order_id(order_id)

            if result['status'] != 0:
                return 534, "order process error"
            duration = (datetime.datetime.now() - result['create_time']).total_seconds()
            if duration > self.duration_limit:
                store_id = result['store_id']
                booklist = self.db['new_order_detail'].find({'order_id': order_id}, {'book_id':1, 'count':1, 'price':1})
                for row in booklist:
                    book_id = row['book_id']
                    count = row['count']
                    bookresult = self.db['store'].update_one({'store_id': store_id, 'book_id': book_id}, {'$inc': {'stock_level': count}})
                    if bookresult.matched_count == 0:
                        return 536, "invalid store_id and book_id"
                self.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 4}})
                return 534, "order process error"

            order_id = result['order_id']
            buyer_id = result['user_id']
            store_id = result['store_id']

            if buyer_id != user_id:
                return error.error_authorization_fail()

            result = self.db['user'].find_one({'user_id': buyer_id}, {'balance':1, 'password':1})
            if result is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = result['balance']
            if password != result['password']:
                return error.error_authorization_fail()

            result = self.db['user_store'].find_one({'store_id': store_id}, {'store_id':1, 'user_id':1})
            if result is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = result['user_id']

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            result = self.db['new_order_detail'].find({'order_id': order_id}, {'book_id':1, 'count':1, 'price':1})
            total_price = 0
            for row in result:
                count = row['count']
                price = row['price']
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            result = self.db['user'].update_one({'user_id': buyer_id, 'balance': {'$gte': total_price}}, {'$inc': {'balance': -total_price}})
            if result.modified_count == 0:
                return error.error_not_sufficient_funds(order_id)

            result = self.db['user'].update_one({'user_id': seller_id}, {'$inc': {'balance': total_price}})
            if result.modified_count == 0:
                return error.error_non_exist_user_id(seller_id)
            
            result = self.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 1}})
            if result.modified_count == 0:
                return error.error_invalid_order_id(order_id)

            # result = self.db['new_order'].delete_one({'order_id': order_id})
            # if result.deleted_count == 0:
            #     return error.error_invalid_order_id(order_id)

            # result = self.db['new_order_detail'].delete_many({'order_id': order_id})
            # if result.deleted_count == 0:
            #     return error.error_invalid_order_id(order_id)

        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
    #     conn = self.conn
    #     try:
    #         cursor = conn.execute("SELECT order_id, user_id, store_id FROM new_order WHERE order_id = ?", (order_id,))
    #         row = cursor.fetchone()
    #         if row is None:
    #             return error.error_invalid_order_id(order_id)

    #         order_id = row[0]
    #         buyer_id = row[1]
    #         store_id = row[2]

    #         if buyer_id != user_id:
    #             return error.error_authorization_fail()

    #         cursor = conn.execute("SELECT balance, password FROM user WHERE user_id = ?;", (buyer_id,))
    #         row = cursor.fetchone()
    #         if row is None:
    #             return error.error_non_exist_user_id(buyer_id)
    #         balance = row[0]
    #         if password != row[1]:
    #             return error.error_authorization_fail()

    #         cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = ?;", (store_id,))
    #         row = cursor.fetchone()
    #         if row is None:
    #             return error.error_non_exist_store_id(store_id)

    #         seller_id = row[1]

    #         if not self.user_id_exist(seller_id):
    #             return error.error_non_exist_user_id(seller_id)

    #         cursor = conn.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = ?;", (order_id,))
    #         total_price = 0
    #         for row in cursor:
    #             count = row[1]
    #             price = row[2]
    #             total_price = total_price + price * count

    #         if balance < total_price:
    #             return error.error_not_sufficient_funds(order_id)

    #         cursor = conn.execute("UPDATE user set balance = balance - ?"
    #                               "WHERE user_id = ? AND balance >= ?",
    #                               (total_price, buyer_id, total_price))
    #         if cursor.rowcount == 0:
    #             return error.error_not_sufficient_funds(order_id)

    #         cursor = conn.execute("UPDATE user set balance = balance + ?"
    #                               "WHERE user_id = ?",
    #                               (total_price, buyer_id))

    #         if cursor.rowcount == 0:
    #             return error.error_non_exist_user_id(buyer_id)

    #         cursor = conn.execute("DELETE FROM new_order WHERE order_id = ?", (order_id, ))
    #         if cursor.rowcount == 0:
    #             return error.error_invalid_order_id(order_id)

    #         cursor = conn.execute("DELETE FROM new_order_detail where order_id = ?", (order_id, ))
    #         if cursor.rowcount == 0:
    #             return error.error_invalid_order_id(order_id)

    #         conn.commit()

    #     except sqlite.Error as e:
    #         return 528, "{}".format(str(e))

    #     except BaseException as e:
    #         return 530, "{}".format(str(e))

    #     return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            result = self.db['user'].find_one({'user_id': user_id}, {'password':1})
            if result is None:
                return error.error_authorization_fail()

            if result.get('password') != password:
                return error.error_authorization_fail()

            result = self.db['user'].update_one({'user_id': user_id}, {'$inc': {'balance': add_value}})
            if result.matched_count == 0:
                return error.error_non_exist_user_id(user_id)
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # def add_funds(self, user_id, password, add_value) -> (int, str):
    #     try:
    #         cursor = self.conn.execute("SELECT password  from user where user_id=?", (user_id,))
    #         row = cursor.fetchone()
    #         if row is None:
    #             return error.error_authorization_fail()

    #         if row[0] != password:
    #             return error.error_authorization_fail()

    #         cursor = self.conn.execute(
    #             "UPDATE user SET balance = balance + ? WHERE user_id = ?",
    #             (add_value, user_id))
    #         if cursor.rowcount == 0:
    #             return error.error_non_exist_user_id(user_id)

    #         self.conn.commit()
    #     except sqlite.Error as e:
    #         return 528, "{}".format(str(e))
    #     except BaseException as e:
    #         return 530, "{}".format(str(e))

    #     return 200, "ok"

    def send_out_delivery(self, user_id, store_id, order_id) -> (int, str):
        try:
            result = self.db['new_order'].find_one({'order_id': order_id}, {'store_id':1, 'status':1})
            if result is None:
                return error.error_invalid_order_id(order_id)
            
            if store_id != result['store_id']:
                return 531, "order mismatch(store)"
            if result['status'] != 1:
                return 534, "order process error"
            
            result = self.db['user_store'].find_one({'user_id': user_id, 'store_id': store_id})
            if result is None:
                return 532, "order mismatch(seller)"
            
            result = self.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 2}})
            if result.matched_count == 0:
                return error.error_invalid_order_id(order_id)
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
    
    def take_delivery(self, user_id, token, order_id) -> (int, str):
        try:
            code, message = User().check_token(user_id, token)
            if code != 200:
                return code, message
            
            result = self.db['new_order'].find_one({'order_id': order_id}, {'user_id':1, 'status':1})
            if result is None:
                return error.error_invalid_order_id(order_id)
            
            if user_id != result['user_id']:
                return 533, "order mismatch(buyer)"
            if result['status'] != 2:
                return 534, "order process error"
            
            result = self.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 3}})
            if result.matched_count == 0:
                return error.error_invalid_order_id(order_id)
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def order_cancel(self, user_id, token, order_id) -> (int, str):
        try:
            code, message = User().check_token(user_id, token)
            if code != 200:
                return code, message
            
            result = self.db['new_order'].find_one({'order_id': order_id}, {'user_id':1, 'store_id':1, 'status':1})
            if result is None:
                return error.error_invalid_order_id(order_id)
            
            if user_id != result['user_id']:
                return 533, "order mismatch(buyer)"
            if result['status'] > 1:
                return 535, "order cancellation failed"
            
            store_id = result['store_id']

            total_price = 0
            booklist = self.db['new_order_detail'].find({'order_id': order_id}, {'book_id':1, 'count':1, 'price':1})
            for row in booklist:
                book_id = row['book_id']
                count = row['count']
                price = row['price']
                bookresult = self.db['store'].update_one({'store_id': store_id, 'book_id': book_id}, {'$inc': {'stock_level': count}})
                if bookresult.matched_count == 0:
                    return 536, "invalid store_id and book_id"
                total_price = total_price + count * price

            storeresult = self.db['user_store'].find_one({'store_id': store_id}, {'user_id':1})
            if storeresult is None:
                return error.error_non_exist_store_id(store_id)
            
            seller_id = storeresult['user_id']
            if result['status'] == 1:
                userresult = self.db['user'].update_one({'user_id': user_id}, {'$inc': {'balance': total_price}})
                if userresult.matched_count == 0:
                    return error.error_non_exist_user_id(user_id)
                userresult = self.db['user'].update_one({'user_id': seller_id}, {'$inc': {'balance': -total_price}})
                if userresult.matched_count == 0:
                    return error.error_non_exist_user_id(user_id)
            
            self.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 4}})
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
    
    def order_query(self, user_id, token) -> (int, str, list):
        try:
            code, message = User().check_token(user_id, token)
            if code != 200:
                return code, message, ""
            
            orders = []
            result = self.db['new_order'].find({'user_id': user_id}, {'_id':0})
            for order in result:
                order_details = []
                order_id = order['order_id']
                store_id = order['store_id']
                booklist = self.db['new_order_detail'].find({'order_id': order_id}, {'_id':0})
                duration = (datetime.datetime.now() - order['create_time']).total_seconds()
                for row in booklist:
                    book_id = row['book_id']
                    count = row['count']
                    if order['status'] <= 1 and duration > self.duration_limit:
                        bookresult = self.db['store'].update_one({'store_id': store_id, 'book_id': book_id}, {'$inc': {'stock_level': count}})
                        if bookresult.matched_count == 0:
                            return 536, "invalid store_id and book_id", ""
                    order_details.append(row)

                if order['status'] <= 1 and duration > self.duration_limit:
                    self.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 4}})
                    order['status'] = 4
                order['order_details'] = order_details
                orders.append(order)
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", orders