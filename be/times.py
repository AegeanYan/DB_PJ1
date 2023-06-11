import datetime
from be.model.buyer import Buyer
from be.model import store
from be.model.store import users, user_store, stores, new_order, new_order_detail

def regular_inspection():
    duration_limit = 10

    session = store.get_db_conn()
    result = session.query(new_order).filter(new_order.status == 0).all()
    for row in result:
        order_id = row.order_id
        duration = (datetime.datetime.now() - row.create_time).total_seconds()
        if duration > duration_limit:
            store_id = row.store_id
            booklist = session.query(new_order_detail).filter(new_order_detail.order_id == order_id).all()
            for bookrow in booklist:
                book_id = bookrow.book_id
                count = bookrow.count
                session.query(stores).filter(stores.store_id == store_id, stores.book_id == book_id).update({stores.stock_level: stores.stock_level + count})
                session.commit()
            session.query(new_order).filter(new_order.order_id == order_id).update({new_order.status: 4})
            session.commit()