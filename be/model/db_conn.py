from sqlalchemy.orm import session
from be.model.store import users, user_store, stores, new_order, new_order_detail, get_db_conn

class DBConn:
    def __init__(self):
        self.session = get_db_conn()

    def user_id_exist(self, user_id):
        result = self.session.query(users).filter(users.user_id == user_id).all()
        return len(result) != 0

        
    def is_my_store(self, user_id, store_id):
        result = self.session.query(user_store).filter(user_store.user_id == user_id, user_store.store_id == store_id).all()
        return len(result) != 0


    def book_id_exist(self, store_id, book_id):
        result = self.session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id).all()
        return len(result) != 0


    def store_id_exist(self, store_id):
        result = self.session.query(user_store).filter(user_store.store_id == store_id).all()
        return len(result) != 0
