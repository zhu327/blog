#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

import json, functools

from transwarp.web import ctx

class APIError(StandardError):
    def __init__(self, error, data='', message=''):
        super(StandardError, self_).__init__(message)
        self.error = error
        self.data = data
        self.message = massage

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
            r = json.dumps(func(*args, **kw))
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
