import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import json
from be.model import store
from be.model.store import users, user_store, stores, new_order, new_order_detail
from fe.access.book import books
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import or_


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.encode("utf-8").decode("utf-8")


def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)
        self.session = store.get_db_conn()

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False


    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            new_user = users(user_id = user_id, password = password, balance = 0, token = token, terminal = terminal)
            self.session.add(new_user)
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            return error.error_exist_user_id(user_id)
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"


    
    def check_token(self, user_id: str, token: str) -> (int, str):
        result = self.session.query(users).filter(users.user_id == user_id).all()
        if len(result) == 0:
            return error.error_authorization_fail()
        db_token = result[0].token
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        result = self.session.query(users).filter(users.user_id == user_id).all()
        if len(result) == 0:
            return error.error_authorization_fail()

        if password != result[0].password:
            return error.error_authorization_fail()

        return 200, "ok"


    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            self.session.query(users).filter(users.user_id == user_id).update({users.token: token, users.terminal: terminal})
            self.session.commit()
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token


    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            self.session.query(users).filter(users.user_id == user_id).update({users.token: dummy_token, users.terminal: terminal})
            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"


    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            self.session.query(users).filter(users.user_id == user_id).delete()
            self.session.commit()

        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"


    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            self.session.query(users).filter(users.user_id == user_id).update({users.password: new_password, users.token: token, users.terminal: terminal})
            self.session.commit()
            
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"


    def search_for_book(self, user_id: str, target: str, store_id: str = '-1') -> (int, str, list):
        try:
            book_list = []
            if store_id != '-1':
                if not self.store_id_exist(store_id):
                    return error.error_non_exist_store_id(store_id),''
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id),''
            
            result = self.session.query(books).filter(or_(
                books.title.ilike(f'%{target}%'),
                books.author.ilike(f'%{target}%'),
                books.publisher.ilike(f'%{target}%'),
                books.original_title.ilike(f'%{target}%'),
                books.translator.ilike(f'%{target}%'),
                books.author_intro.ilike(f'%{target}%'),
                books.book_intro.ilike(f'%{target}%'),
                books.content.ilike(f'%{target}%'),
                books.tags.ilike(f'%{target}%')
            )).limit(10)
            for book in result:
                book_list.append(book.to_dict())
            
            i = 1
            while(True):
                if len(list(result)) < 10:
                    break
                result = self.session.query(books).filter(or_(
                    books.title.ilike(f'%{target}%'),
                    books.author.ilike(f'%{target}%'),
                    books.publisher.ilike(f'%{target}%'),
                    books.original_title.ilike(f'%{target}%'),
                    books.translator.ilike(f'%{target}%'),
                    books.author_intro.ilike(f'%{target}%'),
                    books.book_intro.ilike(f'%{target}%'),
                    books.content.ilike(f'%{target}%'),
                    books.tags.ilike(f'%{target}%')
                )).offset(int(10*i)).limit(10)
                i += 1
                for book in result:
                    book_list.append(book.to_dict())
            book_ids = []
            for book in book_list:
                book_ids.append(book.id)
            book_ids = set(book_ids)
            result = []
            if store_id == '-1':
                for book_id in book_ids:
                    book = self.session.query(stores).filter(stores.book_id == book_id).all()
                    for cur_book in book:
                        result.append(cur_book.to_dict())
            else:
                for book_id in book_ids:
                    book = self.session.query(stores).filter(stores.book_id == book_id, stores.store_id == store_id).all()
                    for cur_book in book:
                        result.append(cur_book.to_dict())
        except SQLAlchemyError as e:
            self.session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok", result