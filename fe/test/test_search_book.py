import pytest

from fe.access.buyer import Buyer
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access import seller
from fe.access import book
from fe.access import auth
from fe import conf
import uuid


class TestSearchBook:
    seller_id: str
    store_id: str
    buyer_id: str
    password:str
    buy_book_info_list: [book.Book]
    total_price: int
    order_id: str
    buyer: Buyer

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_payment_seller_id_{}".format(str(uuid.uuid1()))

        self.store_id = "test_payment_store_id_{}".format(str(uuid.uuid1()))
        self.store_id_ = "test_payment_store_id1_{}".format(str(uuid.uuid1()))
        self.store_id__ = "test_payment_store_id1_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_payment_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        self.seller = gen_book.seller
        code = self.seller.create_store(self.store_id_)
        assert code == 200
        code = self.seller.create_store(self.store_id__)
        assert code == 200
        book_db = book.BookDB()
        self.books = book_db.get_book_info(0, 10)
        for b in self.books:
            code = self.seller.add_book(self.store_id_, 0, b)
            assert code == 200
            book_db = book.BookDB()
        self.books = book_db.get_book_info(5, 10)
        for b in self.books:
            code = self.seller.add_book(self.store_id__, 0, b)
            assert code == 200
        yield

    def test_ok(self):
        a = auth.Auth(conf.URL)
        code, books = a.search(self.seller_id, '美丽心灵 毛泽东', '-1')
        assert code == 200
        print(books)
    
