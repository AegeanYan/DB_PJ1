import pytest

from fe.access.buyer import Buyer
from fe.access.seller import Seller
from fe.test.gen_book_many import GenBookMany
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid
import time


class TestOrder:
    seller_id: str
    store_id: str
    buyer_id: str
    password:str
    buy_book_info_list: [Book]
    total_price: int
    order_id: str
    buyer: Buyer

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_order_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBookMany(self.seller_id, self.store_id)
        ok, self.buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=1)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        # add stock
        self.seller = gen_book.seller
        for now_book in self.buy_book_id_list:
            self.seller.add_stock_level(self.seller_id, self.store_id, now_book[0], now_book[1] * 9)

        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        code, self.order_id_ordered_not_paid = b.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code, self.order_id_paid_not_sent = b.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code, self.order_id_sent_not_received = b.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code, self.order_id_canceled = b.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code, self.order_id_received = b.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        code, self.order_id_cancel_before_pay = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code, self.order_id_cancel_after_deliver = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        code , self.order_id_auto_cancel = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        code, self.order_regular_inspection = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        yield

    def test_ok(self):
        code = self.buyer.add_funds(100000000)
        assert code == 200
        code = self.buyer.payment(self.order_id_received)
        assert code == 200
        code = self.buyer.payment(self.order_id_sent_not_received)
        assert code == 200
        code = self.buyer.payment(self.order_id_canceled)
        assert code == 200
        code = self.buyer.payment(self.order_id_paid_not_sent)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id,self.store_id,self.order_id_sent_not_received)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id,self.store_id,self.order_id_received)
        assert code == 200
        code = self.buyer.order_cancel(self.order_id_canceled)
        assert code == 200
        code = self.buyer.take_delivery(self.order_id_received)
        assert code == 200
        code, order = self.buyer.order_query()
        assert code == 200
        print(order)

    def test_cancel(self):
        code = self.buyer.add_funds(100000000)
        code = self.buyer.order_cancel(self.order_id_cancel_before_pay)
        assert code == 200
        code = self.buyer.payment(self.order_id_cancel_after_deliver)
        assert code == 200
        code = self.buyer.send_out_delivery(self.seller_id,self.store_id,self.order_id_cancel_after_deliver)
        assert code == 200
        code = self.buyer.order_cancel(self.order_id_cancel_after_deliver)
        assert code != 200
        code, order = self.buyer.order_query()
        assert code == 200
        print(order)
        
    def test_auto_cancel(self):
        time.sleep(15)
        code, order = self.buyer.order_query()
        assert code == 200
        print(order)

    def test_regular_inspection(self):
        time.sleep(15)
        code = self.buyer.payment(self.order_regular_inspection)
        assert code == 534

