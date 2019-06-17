from psycopg2 import sql
import psycopg2
            
def get_read_filter_query(table_name:str, columns:tuple, filter_on: str):
    """ generates sql """
    columns_c = sql.SQL(',').join([sql.Identifier(c) for c in columns])
    query_c = sql.SQL('select {0} from {1} where {2}=%s' ).format(
        columns_c, sql.Identifier(table_name), sql.Identifier(filter_on))
    return query_c

