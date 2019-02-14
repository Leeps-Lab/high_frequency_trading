import os

class BookLogger():
    def __init__(self, book_logfile):
        booklog = os.path.join(os.getcwd(), book_logfile)
        self.book_logfile = booklog

    def book_to_dict(self, book, order_store):
        return {'Bids':[{'price':b.price, 
                        'orders':[(id, q) for (id,q) in b.order_q.items()] } 
                    for b in book.bids.ascending_items()], 
                'Asks':[{'price':a.price, 
                        'orders':[(id, q) for (id,q) in a.order_q.items()]} 
                for a in book.asks.ascending_items()]} 

    def log_book(self, book, timestamp, order_store):
        with open(self.book_logfile, "a") as logfile:
            logfile.writelines([str({'timestamp':timestamp, 
                            'book':self.book_to_dict(book, order_store)}), '\n'])

    def log_book_order(self, book, order, timestamp, order_store):
        with open(self.book_logfile, "a") as logfile:
            logfile.writelines([str({'timestamp':timestamp, 
                                'order':str(order), 
                                'book':self.book_to_dict(book, order_store)}), '\n']) 
