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

import threading, logging

# 数据库引擎对象:
class _Engine(obeject):
    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()

engine = None

# 持有数据库连接的上下问对象:
class _DbCtx(obeject):
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

# 事务上下文对象:
class _TransactionCxt(object):
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
                else:
                    self.rollback()
        finally:
            if self.should_cleanup == 0:
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    import doctest
    doctest.testmod()

