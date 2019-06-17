import json
import time
from collections import abc
from twisted.python import log
from twisted.internet import reactor
import psycopg2
try:
    from hft.exogenous_event_emitter import db
except ImportError:
    import db


class WSMessageEmitter:

    def __init__(self, session_id, type_code, raw_data=None, columns=None, 
            table_name=None, filter_on=None, filter_value=None):
        self.session_id = session_id
        self.type_code = type_code
        self.ws_conn = None
        if raw_data:
            if not isinstance(raw_data, abc.Iterable):
                raise Exception('raw data is not iterable')
            else:
                self.data = raw_data
        else:
            kws = (filter_value, filter_value, table_name, columns)
            if None in kws:
                raise Exception('no raw data is given but db parameters missing:'
                    '%s' % kws )
            else:
                self.table_name = table_name
                self.columns = columns
                self.filter_on = filter_on
                self.filter_value = filter_value
    
    def read_from_db(self, **kwargs):
        with psycopg2.connect(**kwargs) as conn:
            query = db.get_read_filter_query(self.table_name, self.columns, 
                filter_on=self.filter_on)
            query_string = query.as_string(conn)
            log.msg('query: %s' % query_string)
            with conn.cursor() as curs:
                curs.execute(query, (self.filter_value, ))
                data = curs.fetchall()
        if not data:
            raise Exception('not found: q: %s' % query)
        else:
            self.data = data

    
    def run(self, retries=0):
        while not self.data:
            log.msg('waiting for data..')
            updated_retries = retries + 1
            reactor.callLater(2 ** retries / 10, self.run, retries=updated_retries)
            return
        rows = iter(self.data)
        if self.ws_conn is None:
            reactor.callLater(2 ** retries / 10, self.run, retries=retries + 1)
            log.msg('waiting for connection..%s retries..' % retries)
        else:
            while True:
                try:
                    next_row = next(rows)
                except StopIteration:
                    break
                else:
                    # assume first element
                    # is message time
                    arrival_time = next_row[0]
                    dict_msg = {c: next_row[ix] for ix, c in enumerate(self.columns)}
                    dict_msg['type'] = self.type_code
                    payload = json.dumps(dict_msg, ensure_ascii=False).encode('utf8')
                    reactor.callLater(arrival_time, self.ws_conn.sendMessage, 
                        payload, False)


                
                





