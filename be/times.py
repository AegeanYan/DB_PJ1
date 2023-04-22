import datetime
from be.model.buyer import Buyer

def regular_inspection():
    b = Buyer()
    result = b.db['new_order'].find({'status': 0}, {'order_id':1, 'store_id':1, 'create_time':1})
    for row in result:
        order_id = row['order_id']
        duration = (datetime.datetime.now() - row['create_time']).total_seconds()
        if duration > b.duration_limit:
            store_id = row['store_id']
            booklist = b.db['new_order_detail'].find({'order_id': order_id}, {'book_id':1, 'count':1})
            for row in booklist:
                book_id = row['book_id']
                count = row['count']
                b.db['store'].update_one({'store_id': store_id, 'book_id': book_id}, {'$inc': {'stock_level': count}})
            b.db['new_order'].update_one({'order_id': order_id}, {'$set': {'status': 4}})