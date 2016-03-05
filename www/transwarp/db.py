#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'zhu327'

'''
MySQL数据库操作封装
实例:
from transwarp import db

# 创建数据库链接引擎，然后就可以直接调用数据操作
db.create_engine(user='root', password='password', host='host', port=3306, database='test')

# 直接操作数据查询，返回列表，列表元为字典为查询的每一行数据
user = db.select('select * from user')
# user =>
# [
#     {'id': 1, 'name': 'Timmy Chu'},
#     ......
# ]

# 执行INSERT DELETE UPDATE返回受影响的行数
n = db.update('insert int user(id, name)' value(?, ?)', 4, 'Jack')
# n =>
# 1
'''

import threading, functools, logging, hashlib
# import pylibmc // 替换memcached为SAE KVDB
import sae.kvdb

class Memcached(threading.local):
    def __init__(self):
        self._mc = lambda :sae.kvdb.Client()
        self.con = None

    def _connect(self):
        if not self.con:
            self.con = self._mc()

    def clean(self):
        if self.con:
            self.con.disconnect_all()
            self.con = None

    def get(self, sql, args):
        key = self._key(sql, args)
        logging.info('MC get %s' % key)
        self._connect()
        return self.con.get(key)

    def set(self, sql, args, data):
        key = self._key(sql, args)
        logging.info('MC set %s' % key)
        self._connect()
        self.con.set(key, data)

    def flush(self):
        self._connect()
        keys = self.con.getkeys_by_prefix('', 10000)
        map(self.con.delete, keys)

    def _key(self, sql, args):
        return hashlib.md5(sql % args).hexdigest()


mc = Memcached()

# 数据库引擎对象，包装了数据库连接函数
class _Engine(object):
    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()

engine = None

def create_engine(user, passwd, db, host='127.0.0.1', port=3306, **kw):
    import MySQLdb
    global engine
    if engine:
        return
    params = dict(user=user, passwd=passwd, db=db, host=host, port=port)
    defaults = dict(use_unicode=True, charset='utf8')
    for k in kw.iterkeys():
        if k in defaults:
            defaults.pop(k)
    params.update(defaults)
    params.update(kw)
    engine = _Engine(lambda: MySQLdb.connect(**params))
    logging.info('MySQL connect %s' % params)
    logging.info('create engine %s' % id(engine))

# 持有数据库连接的上下问对象:
class _DbCtx(threading.local):
    def __init__(self):
        self.connect = None
        self.transactions = 0

    def is_init(self):
        return not self.connect is None

    def init(self):
        self.connect = _LasyConnection()
        self.transactions = 0

    def cleanup(self):
        self.connect.cleanup()
        self.connect = None

    def cursor(self):
        return self.connect.cursor()

_db_cxt = _DbCtx()

# 数据库建立连接，封装基础的数据库操作动作
class _LasyConnection(object):
    def __init__(self):
        self.connect = None

    def cleanup(self):
        if self.connect:
            self.connect.close()
            logging.info('close MySQL connect %s' % id(self.connect))
            self.connect = None

    def cursor(self):
        global engine
        if not self.connect:
            self.connect = engine.connect()
            logging.info('create MySQL connect %s' % id(self.connect))
        return self.connect.cursor()

    def commit(self):
        self.connect.commit()

    def rollback(self):
        self.connect.rollback()

class _ConnectionCxt(object):
    def __enter__(self):
        global _db_cxt
        self.shoud_cleanup = False
        if not _db_cxt.is_init():
            _db_cxt.init()
            self.shoud_cleanup = True
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_cxt
        if self.shoud_cleanup:
            _db_cxt.cleanup()

def connection():
    return _ConnectionCxt()

def with_connection(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with connection():
            return func(*args, **kw)
    return _wrapper

# 事务上下文对象:
class _TransactionCxt(object):
    '''
    Transaction test

    >>> user1 = dict(id=51,name='ta',passwd='tata',email='ta@test.org')
    >>> user2 = dict(id=52,name='haha',passwd='hahahhah',email='ta@test.org')
    >>> with _TransactionCxt():
    ...     insert('user', **user1)
    ...     insert('user', **user2)
    1L
    1L
    >>> l = select('select `id` from `user`')
    >>> len(l)
    2
    '''
    def __enter__(self):
        global _db_cxt
        self.should_cleanup = False
        if not _db_cxt.is_init():
            _db_cxt.init()
            self.should_cleanup = True
        _db_cxt.transactions = _db_cxt.transactions + 1
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_cxt
        _db_cxt.transactions = _db_cxt.transactions - 1
        try:
            if _db_cxt.transactions == 0:
                if exctype == None:
                    self.commit()
                    logging.info('transaction commit')
                else:
                    self.rollback()
        finally:
            if self.should_cleanup:
                _db_cxt.cleanup()

    def commit(self):
        global _db_cxt
        try:
            _db_cxt.connect.commit()
        except:
            _db_cxt.connect.rollback()
            raise

    def rollback(self):
        global _db_cxt
        _db_cxt.connect.rollback()

def transaction():
    return _TransactionCxt()

@with_connection
def select(sql, *args):
    '''
    Execute select SQL and return list or empty list if no result.

    >>> execute('insert into `user` (`id`,`name`,`email`,`passwd`) values (?,?,?,?)', 200, 'Wall.E', 'wall.e@test.org', 'back-to-earth')
    1L
    >>> execute('insert into `user` (`id`,`name`,`email`,`passwd`) values (?,?,?,?)', 201, 'Eva','eva@test.org', 'back-to-earth')
    1L
    >>> L = select('select * from user where id=?', 900900900)
    >>> L
    []
    >>> L = select('select * from user where id=?', 200)
    >>> L[0]['email']
    u'wall.e@test.org'
    >>> L = select('select * from user where passwd=? order by id desc', 'back-to-earth')
    >>> L[0]['name']
    u'Eva'
    >>> L[1]['name']
    u'Wall.E'
    '''
    global _db_cxt
    sql = sql.replace('?', '%s')
    logging.info('select sql: %s, args: %s' % (sql, args))
    cursor = None
    try:
        r = mc.get(sql, args)
        if r:
            logging.info('MC get data')
            return r
        cursor = _db_cxt.cursor()
        cursor.execute(sql, args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        r = [dict(zip(names, x)) for x in cursor.fetchall()]
        mc.set(sql, args, r)
        return r
    finally:
        mc.clean()
        if cursor:
            cursor.close()

@with_connection
def execute(sql, *args):
    global _db_cxt
    sql = sql.replace('?', '%s')
    logging.info('execute sql: %s, args: %s' % (sql, args))
    cursor = None
    try:
        mc.flush()
        cursor = _db_cxt.cursor()
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_cxt.transactions == 0:
            _db_cxt.connect.commit()
            logging.info('auto commit')
        return r
    finally:
        mc.clean()
        if cursor:
            cursor.close()

def insert(table, **kw):
    '''
    Insert date to table

    >>> user1 = dict(id=101, name='Timmy', email='tim@test.org', passwd='h1w2d3b4')
    >>> user2 = dict(id=102, name='Tom', email='tom@test.org', passwd='tomlike')
    >>> insert('user', **user1)
    1L
    >>> insert('user', **user2)
    1L
    >>> l = select('select * from `user` where `id`=?', 101)
    >>> l[0]['passwd']
    u'h1w2d3b4'
    >>> l = select('select * from `user` where `id`=?', 102)
    >>> l[0]['email']
    u'tom@test.org'
    >>> insert('user', **user1)
    Traceback (most recent call last):
      ...
    IntegrityError: (1062, "Duplicate entry '101' for key 'PRIMARY'")
    '''
    names, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join('`%s`' % x for x in names), \
        ','.join('?' for i in range(len(names))))
    return execute(sql, *args)

@with_connection
def insert_id(table, **kw):
    names, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join('`%s`' % x for x in names), \
        ','.join('?' for i in range(len(names))))
    global _db_cxt
    sql = sql.replace('?', '%s')
    logging.info('execute sql: %s, args: %s' % (sql, args))
    cursor = None
    try:
        mc.flush()
        cursor = _db_cxt.cursor()
        cursor.execute(sql, args)
        r = int(cursor.lastrowid)
        if _db_cxt.transactions == 0:
            _db_cxt.connect.commit()
            logging.info('auto commit')
        return r
    finally:
        mc.clean()
        if cursor:
            cursor.close()

def select_int(sql, *args):
    '''
    select row count

    >>> select_int('select count(*) from `user`')
    6L
    >>> select_int('select count(id) from `user` where `id`=?', 101)
    1L
    '''
    l = select(sql, *args)
    if len(l) != 1:
        raise
    return l[0].values()[0]

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    create_engine('root', '', 'test')
    execute('drop table if exists user')
    execute('create table user (id int primary key, name text, email text, passwd text)')
    import doctest
    doctest.testmod()
