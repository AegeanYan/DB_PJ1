import sqlite3 as sqlite
from sqlalchemy.exc import SQLAlchemyError
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
import datetime
from be.model.user import User
import numpy as np
from be.model.store import users, user_store, stores, new_order, new_order_detail, get_db_conn

class Buyer(db_conn.DBConn):
    def __init__(self, limit = np.inf):
        db_conn.DBConn.__init__(self)
        self.duration_limit = 10
        self.session = get_db_conn()


    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            total_price = 0
            for book_id, count in id_and_count:
                result = self.session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id).all()
                if len(result) == 0:
                    return error.error_non_exist_book_id(book_id) + (order_id, )

                stock_level = result[0].stock_level
                book_info = result[0].book_info
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                total_price += price * count
                self.session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id, stores.stock_level >= count).update({stores.stock_level: stores.stock_level - count})
                self.session.commit()
                
                order_detail = new_order_detail(order_id = uid, book_id = book_id, count = count, price = price)
                self.session.add(order_detail)
                self.session.commit()

            order = new_order(order_id = uid, store_id = store_id, user_id = user_id, status = 0, create_time = datetime.datetime.now(), total_price = total_price)
            self.session.add(order)
            self.session.commit()
            order_id = uid
        except SQLAlchemyError as e:
            self.session.rollback()
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id



    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        print(1)
        session = self.session
        try:
            result = session.query(new_order).filter(new_order.order_id == order_id).all()
            if len(result) == 0:
                return error.error_invalid_order_id(order_id)
            if result[0].status != 0:
                return 534, "order process error"

            duration = (datetime.datetime.now() - result[0].create_time).total_seconds()
            if duration > self.duration_limit:
                store_id = result[0].store_id
                booklist = session.query(new_order_detail).filter(new_order_detail.order_id == order_id).all()
                for bookrow in booklist:
                    book_id = bookrow.book_id
                    count = bookrow.count
                    session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id).update({stores.stock_level: stores.stock_level + count})
                    session.commit()

                session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 4})
                session.commit()
                return 534, "order process error"


            buyer_id = result[0].user_id
            store_id = result[0].store_id
            print("here!")
            if buyer_id != user_id:
                return error.error_authorization_fail()

            result = session.query(users).filter(users.user_id == user_id).all()
            if len(result) == 0:
                return error.error_non_exist_user_id(buyer_id)
            balance = result[0].balance
            if password != result[0].password:
                return error.error_authorization_fail()

            result = session.query(user_store).filter(user_store.store_id == store_id).all()
            if len(result) == 0:
                return error.error_non_exist_store_id(store_id)

            seller_id = result[0].user_id

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            result = session.query(new_order).filter(new_order.order_id == order_id).all()
            if balance < result[0].total_price:
                return error.error_not_sufficient_funds(order_id)

            total_price = result[0].total_price
            session.query(users).filter(users.user_id == buyer_id).update({users.balance: users.balance - total_price})
            session.commit()
            
            session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 1})
            session.commit()
            
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"



    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            result = self.session.query(users).filter(users.user_id == user_id).all()
            if len(result) == 0:
                return error.error_authorization_fail()

            if result[0].password != password:
                return error.error_authorization_fail()

            self.session.query(users).filter(users.user_id == user_id).update({users.balance: users.balance + add_value})
            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

   
    def send_out_delivery(self, user_id, store_id, order_id) -> (int, str):
        try:
            result = self.session.query(new_order).filter(new_order.order_id == order_id).all()
            if len(result) == 0:
                return error.error_invalid_order_id(order_id)
            
            if store_id != result[0].store_id:
                return 531, "order mismatch(store)"
            if result[0].status != 1:
                return 534, "order process error"
            
            result = self.session.query(user_store).filter(user_store.user_id == user_id, user_store.store_id == store_id).all()
            if len(result) == 0:
                return 532, "order mismatch(seller)"
            
            self.session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 2})
            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        
        return 200, "ok"
    
    
    def take_delivery(self, user_id, token, order_id) -> (int, str):
        try:
            code, message = User().check_token(user_id, token)
            if code != 200:
                return code, message
            
            result = self.session.query(new_order).filter(new_order.order_id == order_id).all()
            if len(result) == 0:
                return error.error_invalid_order_id(order_id)
            
            if user_id != result[0].user_id:
                return 533, "order mismatch(buyer)"
            if result[0].status != 2:
                return 534, "order process error"
            
            store_id = result[0].store_id
            total_price = result[0].total_price
            result = self.session.query(user_store).filter( user_store.store_id == store_id).all()
            if len(result) == 0:
                return error.error_non_exist_store_id(store_id)
            seller_id = result[0].user_id

            self.session.query(users).filter(users.user_id == seller_id).update({users.balance: users.balance + total_price})
            self.session.commit()
            self.session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 3})
            self.session.commit()


            
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        
        return 200, "ok"
    
    def query_order(self, user_id, token) -> (int, str, list):
        try:
            code, message = User().check_token(user_id, token)
            if code != 200:
                return code, message, ""
            
            orders = []
            result = self.session.query(new_order).filter(new_order.user_id == user_id).all()
            for order in result:
                order_details = []
                order_id = order.order_id
                store_id = order.store_id
                booklist = self.session.query(new_order_detail).filter(new_order_detail.order_id == order_id).all()
                duration = (datetime.datetime.now() - order.create_time).total_seconds()
                for row in booklist:
                    book_id = row.book_id
                    count = row.count
                    if order.status <= 1 and duration > self.duration_limit:
                        self.session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id).update({stores.stock_level: stores.stock_level + count})
                        self.session.commit()
                        
                    order_details.append(row.to_dict())

                cur_order = order.to_dict()
                if order.status <= 1 and duration > self.duration_limit:
                    self.session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 4})
                    self.session.commit()
                    cur_order['status'] = 4
                cur_order['order_details'] = order_details
                orders.append(cur_order)
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", orders
    

    def cancel_order(self, user_id, token, order_id) -> (int, str):
        try:
            code, message = User().check_token(user_id, token)
            if code != 200:
                return code, message
            
            result = self.session.query(new_order).filter(new_order.order_id == order_id).all()
            if len(result) == 0:
                return error.error_invalid_order_id(order_id)
            
            if user_id != result[0].user_id:
                return 533, "order mismatch(buyer)"
            if result[0].status > 1:
                return 533, "order cancellation failed"
            
            store_id = result[0].store_id
            
            total_price = result[0].total_price
            
            storeresult = self.session.query(user_store).filter(user_store.store_id == store_id).all()
            if len(storeresult) == 0:
                return error.error_non_exist_store_id(store_id)

            seller_id = storeresult[0].user_id
            if result[0].status == 1:
                self.session.query(users).filter(users.user_id == user_id).update({users.balance: users.balance + total_price})
                self.session.commit()
                
            self.session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 4})
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
    