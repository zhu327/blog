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

import threading, urllib, cgi, datetime, re

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

_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')

class UTC(datetime.tzinfo):
	
    def __init__(self, utc):
        utc = str(utc.strip().upper())
        mt = _RE_TZ.match(utc)
        if mt:
            minus = mt.group(1)=='-'
            h = int(mt.group(2))
            m = int(mt.group(3))
            if minus:
                h, m = (-h), (-m)
            self._utcoffset = datetime.timedelta(hours=h, minutes=m)
            self._tzname = 'UTC%s' % utc
        else:
            raise ValueError('bad utc time zone')

    def utcoffset(self, dt):
        return self._utcoffset

    def dst(self, dt):
        return _TIMEDELTA_ZERO

    def tzname(self, dt):
        return self._tzname

    def __str__(self):
        return 'UTC tzinfo object (%s)' % self._tzname

    __repr__ = __str__

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
        >>> r._cookie
        {'company': 'company=Abc%2C%20Inc.; Max_Age=3600; Path=/'}
        '''
        if not hasattr(self, '_cookie'):
            self._cookie = {}
        l = ['%s=%s' % (urllib.quote(name), urllib.quote(value))]
        if not expires:
            if isinstance(expires, (float, int, long)):
                l.append('Expires=%s' % datetime.datetime.fromtimestamp(expires, UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT'))
            if isinstance(expires, (datetime.datetime, datetime.time)):
                l.append('Expires=%s' % expires.astimezone(UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT'))
        if isinstance(max_age, (int, long)):
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
    '''
    >>> @get('/hello')
    ... def test():
    ...     return None
    >>> test.__route__
    '/hello'
    >>> test.__method__
    'GET'
    '''
    def _decorate(func):
        func.__route__ = path
        func.__method__ = 'GET'
        return func
    return _decorate

# 定义post
def post(path):
    '''
    >>> @post('/admin')
    ... def test():
    ...     return None
    >>> test.__method__
    'POST'
    >>> test.__route__
    '/admin'
    '''
    def _decorate(func):
        func.__route__ = path
        func.__method__ = 'POST'
        return func
    return _decorate

_re_route = re.compile(r'(\:[a-zA-Z_]\w*)') # 匹配只要是有:的就认为是有参数

# 构建参数分离的正则表达式:abc/ 即名为abc的参数
def _build_regex(path):
    '''
    
    >>> _build_regex('/:path') == '^\\/(?P<path>[^\\/]+)$'
    True
    >>> _build_regex('/:id/:user/commout/') == '^\\/(?P<id>[^\\/]+)\\/(?P<user>[^\\/]+)\\/commout\\/$'
    True
    >>> _build_regex('/path/to/:file') == '^\\/path\\/to\\/(?P<file>[^\\/]+)$'
    True
    '''
    re_list = ['^']
    is_var = False
    for v in _re_route.split(path):
        if is_var:
            varname = v[1:]
            re_list.append('(?P<%s>[^\\/]+)' % varname)
        else:
            s = ''
            for c in v:
                if c>='0' and c<='9':
                    s = s + c
                elif c>='a' and c<='z':
                    s = s + c
                elif c>='A' and c<='Z':
                    s = s + c
                else:
                    s = s + '\\' + c # 加\\是转移为\在r'\-'与'\\-'等同，在正则表达式下r'\-'等同'-'
            re_list.append(s)
        is_var = not is_var
    re_list.append('$')
    return ''.join(re_list)

# 定制url路由
class Route(object):
    '''
    >>> @get('/:id/active')
    ... def test(arg):
    ...     print 'test', arg
    >>> r = Route(test)
    >>> r.is_static
    False
    >>> r.match('/tim/active')
    ('tim',)
    >>> r('tim')
    test tim
    '''
    def __init__(self, func):
        self.path = func.__route__
        self.method = func.__method__
        self.is_static = _re_route.search(self.path) is None # 判断path是否有参数
        if not self.is_static:
            self.route = re.compile(_build_regex(self.path)) # 构造参数匹配正则表达式
        self.func = func

    def match(self, path):
        m = self.route.match(path)
        if m:
            return m.groups()
        return None

    def __call__(self, *args):
        return self.func(*args)

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
        self._get_static = {}
        self._post_static = {}

        self._get_dynamic = []
        self._post_dynamic = []

    # 添加一个URL定义
    def add_url(self, func):
        self._check_not_running()
        route = Route(func)
        if route.is_static:
            if route.method == 'GET':
                self._get_static[route.path] = route
            elif route.method == 'POST':
                self._post_static[route.path] = route
        else:
            if route.method == 'GET':
                self._get_dynamic.append(route)
            elif route.method == 'POST':
                self._post_dynamic.append(route)
        logging.info('add route %s ' % route.method+':'+route.path)

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
