#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

'''
首页
@get('/')
def index():
    return '<h1>Index page</h1>'

带参数的URL
@get('/usr/:id')
def show_user(id):
    user = User.get(id)
    return 'hello, %s' % user.name

支持URL拦截器，对权限限制
@interceptor('/manage/')
def check_manage_url(next):
    if current_user.idAdmin():
        return next()
    else:
        raise seeother('signin')

模版接口
@view('index.html')
@get('/')
def index():
    return dict(blogs=get_recent_blogs(), user=get_current_user())

获取request与response
@get('/test')
def test():
    input_data = cxt.request.input()
    ctx.response.content_type = 'text/plain'
    ctx.response.set_cookie('name', 'value', expires=3600)
    return 'result'

重定向
rasie seeother('/signin')
rasie notfound()
'''

import threading, urllib, cgi, datetime

# 全局ThreadLocal对象
ctx = threading.local()

# http 错误类
class HttpError(Exception):
    pass

def _to_unicode(s, encoding='utf-8'):
    return s.decode(encoding)

class MultiFile(object):
    def __init__(self, storage):
        self.filename = storage.filename
        self.file = storage.file

# request 对象
class Request(object):
    
    def __init__(self, environ):
        self._environ = environ

    def _get_raw_input(self):
        if not hasattr(self, '_raw_input'):
            def _convet(item):
                if isinstance(item, list):
                    return [_to_unicode(i.value) for i in item]
                if item.filename:
                    return MultiFile(item)
                return _to_unicode(item.value)
            fs = cgi.FieldStorage(fp=self._environ['wsgi.input'], environ=self._environ, keep_blank_values=True)
            d = {}
            for k in fs.keys():
                d[k] = _convet(fs[k])
            self._raw_input = d
        return self._raw_input

    # 根据key返回value
    def get(self, key, default=None):
        '''
        The same as request[key], but return default value if key is not found.

        >>> from StringIO import StringIO
        >>> r = Request({'REQUEST_METHOD':'POST', 'wsgi.input':StringIO('a=1&b=M%20M&c=ABC&c=XYZ&e=')})
        >>> r.get('a')
        u'1'
        >>> r.get('empty')
        >>> r.get('empty', 'DEFAULT')
        'DEFAULT'
        '''
        return self._get_raw_input().get(key, default)
            


    # 返回key-value的dict
    def input(self, **kw):
        '''

        >>> from StringIO import StringIO
        >>> r = Request({'REQUEST_METHOD':'POST', 'wsgi.input':StringIO('a=1&b=M%20M&c=ABC&c=XYZ&e=')})
        >>> r.get('a')
        u'1'
        >>> i = r.input(x=2008)
        >>> i.get('x')
        2008
        '''
        copy = dict(**kw)
        for k,v in self._get_raw_input().iteritems():
            copy[k] = v[0] if isinstance(v, list) else v
        return copy

    # 返回URL的path
    @property
    def path_info(self):
        return urllib.unquote(self._environ.get('PATH_INFO', ''))

    # 返回request method
    @property
    def method(self):
        '''
        >>> from StringIO import StringIO
        >>> r = Request({'PATH_INFO':'/', 'REQUEST_METHOD':'POST', 'wsgi.input':StringIO('a=1&b=M%20M&c=ABC&c=XYZ&e=')})
        >>> r.path_info
        '/'
        >>> r.method
        'POST'
        '''
        return self._environ['REQUEST_METHOD']

    def _get_headers(self):
        if not hasattr(self, '_headers'):
            d = {}
            for k,v in self._environ.iteritems():
                if k.startswith('HTTP_'):
                    d[k[5:].replace('_', '-')] = _to_unicode(v)
            self._headers = d
        return self._headers
    # 返回HTTP header
    @property
    def headers(self):
        '''

        >>> r = Request({'HTTP_USER_AGENT': 'Mozilla/5.0', 'HTTP_ACCEPT': 'text/html'})
        >>> H = r.headers
        >>> H['ACCEPT']
        u'text/html'
        >>> H['USER-AGENT']
        u'Mozilla/5.0'
        >>> L = H.items()
        >>> L.sort()
        >>> L
        [('ACCEPT', u'text/html'), ('USER-AGENT', u'Mozilla/5.0')]
        '''
        return dict(**self._get_headers())

    def _get_cookie(self):
        if not hasattr(self, '_cookie'):
            d = {}
            c_str = self._environ.get('HTTP_COOKIE')
            if c_str:
                for c in c_str.split(';'):
                    pos = c.find('=')
                    d[c[:pos].strip()] = urllib.unquote(_to_unicode(c[pos+1:]))
            self._cookie = d
        return self._cookie

    # 更加key返回Cookie value
    def cookie(self, name, default=None):
        return self._get_cookie().get(name, default)

    @property
    def cookies(self):
        '''
        >>> r = Request({'HTTP_COOKIE':'A=123; url=http%3A%2F%2Fwww.example.com%2F'})
        >>> r.cookies['A']
        u'123'
        >>> r.cookie('url')
        u'http://www.example.com/'
        '''
        return dict(**self._get_cookie())

UTC_0 = UTC('+00:00')

# response对象
class Response(object):
    def __init__(self):
        self._status = '200 OK'
        self._headers = {'CONTENT-TYPE': 'text/html; charset=utf-8'}
    
    @property
    def headers(self):
        return dict(**self._headers)    

    # 设置header
    def set_header(self, key, value):
        self._headers[key] = value 

    # 设置Cookie
    def set_cookie(self, name, value, max_age=None, expires=None, path='/'):
        '''

        >>> r = Response()
        >>> r.set_cookie('company', 'Abc, Inc.', max_age=3600)
        >>> r._cookies
        {'company': 'company=Abc%2C%20Inc.; Max-Age=3600; Path=/'}
        '''
        if not hasattr(self, '_cookie'):
            self._cookie = {}
        l = ['%s=%s' % (urllib.quote(name), urllib.quote(value))]
        if not expires:
            if isinstance(expires, (float, int, long)):
                l.append('Expires=%s' % datetime.datetime.fromtimestamp(expires, UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT'))
            if isinstance(expires, (datetime.datetime, datetime.time)):
                l.append('Expires=%s' % expires.astimezone(UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT'))
        elif isinstance(max_age, (int, long)):
            l.append('Max_Age=%s' % max_age)
        l.append('Path=%s' % path)
        self._cookie[name] = '; '.join(l)

    # 设置status
    @property
    def status(self):
        return self._status
    @status.setter
    def status(self, value):
        self._status = value

# 定义GET
def get(path):
    pass

# 定义post
def post(path):
    pass

# 定义模版
def view(path):
    pass

# 定义拦截器
def interceptor(pattern):
    pass

# 定义模版引擎
class TemplateEngine(object):
    def __call__(self, path, model):
        pass

# 缺省使用Jinja2
class Jinja2TemplateEngine(TemplateEngine):
    def __init__(self, templ_dir, **kw):
        from jinja2 import Environment, FileSystemLoader
        self._env = Environment(loader=FileSystemLoader(templ_dir), **kw)

    def __call__(self, path, model):
        return self._env.get_template(path).render(**model).encode('utf-8')

class WSGIApplication(object):
    def __init__(self, document_root=None, **kw):
        pass

    # 添加一个URL定义
    def add_url(self, func):
        pass

    # 添加一个Interceptor定义
    def add_interceptor(self, func):
        pass

    # 设置TemplateEngine
    @property
    def template_engine(self):
        pass

    @template_engine.setter
    def template_engine(self, engine):
        pass

    # 返回WSGI处理函数
    def get_wsgi_application(self):
        def wsgi(env, statr_response):
            pass
        return wsgi

    # 开发模式下直接启动服务器
    def run(self, port=9000, host='127.0.0.1'):
        from wsgiref.simple_server import make_server
        server = make_server(host, port, self.get_wsgi_application())
        server.serve_forver()

wsgi = WSGIApplication()

'''
if __name__ == '__main__':
    wsgi.run()

else:
    application = wsgi.get_wsgi_application()
'''

if __name__ == '__main__':
    import doctest
    doctest.testmod()
