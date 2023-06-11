from be.model import error
from be.model import db_conn
from be.model.store import users, user_store, stores, new_order, new_order_detail
from sqlalchemy.exc import SQLAlchemyError
from be.model.store import get_db_conn
class Seller(db_conn.DBConn):

    def __init__(self):
        db_conn.DBConn.__init__(self)
        self.session = get_db_conn()

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            
            new_store = user_store(store_id = store_id, user_id = user_id)
            self.session.add(new_store)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
    
    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            print(0)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            print(1)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)
            print(2)
            if not self.is_my_store(user_id, store_id):
                return error.error_not_my_store(user_id, store_id)

            new_book = stores(store_id = store_id, book_id = book_id, book_info = book_json_str, stock_level = stock_level)
            self.session.add(new_book)
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"


    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            if not self.is_my_store(user_id, store_id):
                return error.error_not_my_store(user_id, store_id)

            self.session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id).update({stores.stock_level: stores.stock_level + add_stock_level})
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"


    
