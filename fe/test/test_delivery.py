
import pytest

from fe.access.buyer import Buyer
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid

class TestDelivery:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_delivery_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_delivery_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_delivery_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        code, self.order_id = b.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num
        yield

    def test_ok(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id, self.store_id, self.order_id)
        assert code == 200
        code = self.buyer.take_delivery(self.order_id)
        print(code)
        assert code == 200
    
    def test_unpaid_send(self):
        code = self.buyer.send_out_delivery(self.seller_id, self.store_id, self.order_id)
        assert code != 200

    def test_error_take(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.take_delivery(self.order_id)
        assert code != 200

    def test_repeat_send_out(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id, self.store_id, self.order_id)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id, self.store_id, self.order_id)
        assert code != 200

    def test_repeat_take(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id, self.store_id, self.order_id)
        assert code == 200
        code = self.buyer.take_delivery(self.order_id)
        assert code == 200
        code = self.buyer.take_delivery(self.order_id)
        assert code != 200
