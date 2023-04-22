from be.model import store


class DBConn:
    def __init__(self):
        # self.conn = store.get_db_conn()
        self.db = store.get_db_mongo()

    def user_id_exist(self, user_id):
        result = self.db['user'].find_one({'user_id': user_id})
        if result is None:
            return False
        else:
            return True

    def is_my_store(self, user_id, store_id):
        result = self.db['user_store'].find_one({'user_id': user_id, 'store_id': store_id})
        if result is None:
            return False
        else:
            return True

    def book_id_exist(self, store_id, book_id):
        result = self.db['store'].find_one({'store_id': store_id, 'book_id': book_id})
        if result is None:
            return False
        else:
            return True
    
    def store_id_exist(self, store_id):
        result = self.db['user_store'].find_one({'store_id': store_id})
        if result is None:
            return False
        else:
            return True

    # def user_id_exist(self, user_id):
    #     cursor = self.conn.execute("SELECT user_id FROM user WHERE user_id = ?;", (user_id,))
    #     row = cursor.fetchone()
    #     if row is None:
    #         return False
    #     else:
    #         return True

    # def book_id_exist(self, store_id, book_id):
    #     cursor = self.conn.execute("SELECT book_id FROM store WHERE store_id = ? AND book_id = ?;", (store_id, book_id))
    #     row = cursor.fetchone()
    #     if row is None:
    #         return False
    #     else:
    #         return True

    # def store_id_exist(self, store_id):
    #     cursor = self.conn.execute("SELECT store_id FROM user_store WHERE store_id = ?;", (store_id,))
    #     row = cursor.fetchone()
    #     if row is None:
    #         return False
    #     else:
    #         return True