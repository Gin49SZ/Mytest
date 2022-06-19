from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from dataclasses import make_dataclass

dbconn_pool = None

def setup(app, dsn):
    global dbconn_pool
    dbconn_pool = ConnectionPool(dsn, min_size=4)

    async def on_startup(app):
        dbconn_pool.open(wait=True)

    async def on_cleanup(app):
        dbconn_pool.close()

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)


'''使用dataclass格式获取数据'''
def dict_row_factory(cursor):
    if cursor.description is None:
        return None
    
    field_names = [c.name for c in cursor.description]
    _dataclass = make_dataclass("Row", field_names)

    def make_row(values):
        return _dataclass(*values)

    return make_row


dsn = "host=localhost dbname=examdb user=examdb"
dbconn_pool = ConnectionPool(dsn, min_size=4)


@contextmanager
def dblock():
    with dbconn_pool.connection() as conn:
        with conn.cursor() as cur:
            try:
                with conn.cursor(row_factory=dict_row_factory) as cur:
                    yield cur
                    conn.commit()
            except:
                conn.rollback()
                raise
            finally:
                pass

