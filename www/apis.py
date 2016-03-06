#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

import json, functools
from datetime import datetime

from transwarp.web import ctx
from config import configs

def date_handler(obj):
    return obj.strftime('%d %b %Y') if isinstance(obj, datetime) else obj

_PAGE_SIZE = configs.get('page').get('page_size')

class APIError(StandardError):
    def __init__(self, error, data='', message=''):
        super(StandardError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('value:invalid', field, message)

class Page(dict):
    def __init__(self, item_count, page_index=1, page_size=_PAGE_SIZE):
        self.__dict__ = self

        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
        if (item_count == 0) or (page_index < 1) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size
        self.has_next = self.page_index < self.page_count
        self.has_previous = self.page_index > 1

# 返回查询好的数据并生成json格式
def api(func):
    '''
    >>> from transwarp.web import ctx, Response
    >>> ctx.response = Response()
    >>> @api
    ... def test():
    ...     return dict(result='ok', status='200')
    >>> test()
    '{"status": "200", "result": "ok"}'
    >>> ctx.response.content_type
    'application/json'
    '''
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        try:
            r = json.dumps(func(*args, **kw), default=date_handler)
        except APIError, e:
            r = json.dumps(dict(error=e.error, date=e.data, message=e.message))
        except Exception, e:
            r = json.dumps(dict(error='internalerror', data=e.__class__.__name__, message=e.message))
        ctx.response.content_type = 'application/json'
        return r
    return _wrapper

if __name__ == '__main__':
    import doctest
    doctest.testmod()
