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

import threading, urllib, cgi, datetime, re, logging, functools, mimetypes, os, sys, traceback

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

_RESPONSE_STATUSES = {
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',

    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',

    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended',
}

_RE_RESPONSE_STATUS = re.compile(r'^\d{3}(\ \w+)?')

_RESPONSE_HEADERS = (
    'Accept-Ranges',
    'Age',
    'Allow',
    'Cache-Control',
    'Connection',
    'Content-Encoding',
    'Content-Language',
    'Content-Length',
    'Content-Location',
    'Content-MD5',
    'Content-Disposition',
    'Content-Range',
    'Content-Type',
    'Date',
    'ETag',
    'Expires',
    'Last-Modified',
    'Link',
    'Location',
    'P3P',
    'Pragma',
    'Proxy-Authenticate',
    'Refresh',
    'Retry-After',
    'Server',
    'Set-Cookie',
    'Strict-Transport-Security',
    'Trailer',
    'Transfer-Encoding',
    'Vary',
    'Via',
    'Warning',
    'WWW-Authenticate',
    'X-Frame-Options',
    'X-XSS-Protection',
    'X-Content-Type-Options',
    'X-Forwarded-Proto',
    'X-Powered-By',
    'X-UA-Compatible',
)

_RESPONSE_HEADER_DICT = dict(zip(map(lambda x: x.upper(), _RESPONSE_HEADERS), _RESPONSE_HEADERS))

_HEADER_X_POWERED_BY = ('X-Powered-By', 'transwarp/1.0')

# 全局ThreadLocal对象
ctx = threading.local()

# http 错误类
class HttpError(Exception):
    '''
    >>> e = HttpError(404)
    >>> e.status
    '404 Not Found'
    '''
    def __init__(self, code):
        super(HttpError, self).__init__()
        self.status = '%d %s' % (code, _RESPONSE_STATUSES[code])

    def headr(self, name, value):
        if not hasattr(self, '_header'):
            self._headr = [_HEADER_X_POWERED_BY]
        self._header.append((name, value))

    @property
    def headers(self):
        if hasattr(self, '_header'):
            return self._header
        return []

    def __str__(self):
        return self.status

    __repr__ = __str__

class RedirectError(HttpError):
    def __init__(self, code, location):
        super(RedirectError, self).__init__(code)
        self.location = location

    def __str__(self):
        return '%s, %s' % (self.status, self.location)

    __repr__ = __str__

def notfound():
    return HttpError(404)

def badrequest():
    return HttpError(400)

def seeother(location):
    return RedirectError(303, location)

def _to_str(s):
    '''
    Convert to str.

    >>> _to_str('s123') == 's123'
    True
    >>> _to_str(u'\u4e2d\u6587') == '\xe4\xb8\xad\xe6\x96\x87'
    True
    >>> _to_str(-123) == '-123'
    True
    '''
    if isinstance(s, str):
        return s
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return str(s)

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

_TIMEDELTA_ZERO = datetime.timedelta(0)

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
        L = [(_RESPONSE_HEADER_DICT.get(k, k), v) for k, v in self._headers.iteritems()]
        if hasattr(self, '_cookie'):
            for v in self._cookie.itervalues():
                L.append(('Set-Cookie', _to_str(v)))
        L.append(_HEADER_X_POWERED_BY)
        return L

    # 设置header
    def set_header(self, name, value):
        key = name.upper()
        if not key in _RESPONSE_HEADER_DICT:
            key = name
        self._headers[key] = _to_str(value)

    def unset_header(self, name):
        '''
        Unset header by name and value.

        >>> r = Response()
        >>> r.content_type
        'text/html; charset=utf-8'
        >>> r.unset_header('CONTENT-type')
        >>> r.content_type
        '''
        key = name.upper()
        if not key in _RESPONSE_HEADER_DICT:
            key = name
        if key in self._headers:
            del self._headers[key]

    @property
    def content_type(self):
        '''
        Get content type from response. This is a shortcut for header('Content-Type').

        >>> r = Response()
        >>> r.content_type
        'text/html; charset=utf-8'
        >>> r.content_type = 'application/json'
        >>> r.content_type
        'application/json'
        '''
        return self._headers.get('CONTENT-TYPE', None)

    @content_type.setter
    def content_type(self, value):
        '''
        Set content type for response. This is a shortcut for set_header('Content-Type', value).
        '''
        if value:
            self.set_header('CONTENT-TYPE', value)
        else:
            self.unset_header('CONTENT-TYPE')

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
        if expires:
            if isinstance(expires, (float, int, long)):
                l.append('Expires=%s' % datetime.datetime.fromtimestamp(expires, UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT'))
            if isinstance(expires, (datetime.datetime, datetime.time)):
                l.append('Expires=%s' % expires.astimezone(UTC_0).strftime('%a, %d-%b-%Y %H:%M:%S GMT'))
        if isinstance(max_age, (int, long)):
            l.append('Max_Age=%s' % max_age)
        l.append('Path=%s' % path)
        self._cookie[name] = '; '.join(l)

    def delete_cookie(self, name):
        self.set_cookie(name, '__delete__', expires=0)

    # 设置status
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):

        if isinstance(value, (int, long)):
            if value>=100 and value<=900:
                st = _RESPONSE_STATUSES.get(value, '')
                if st:
                    self._status = '%d %s' % (value, st)
                else:
                    self._status = str(value)
            else:
                raise ValueError('bad response status code %d' % value)
        elif isinstance(value, basestring):
            if isinstance(value, unicode):
                self._status = value.encode('utf-8')
            if _RE_RESPONSE_STATUS.match(value):
                self._status = value
            else:
                raise ValueError('bad response status code %s' % value)
        else:
            raise TypeError('Bad type of response code.')


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

def _static_file_generator(fpath):
    BLOCK_SIZE = 8192
    with open(fpath, 'rb') as f:
        block = f.read(BLOCK_SIZE)
        while block:
            yield block
            block = f.read(BLOCK_SIZE)

# 静态文件路由
class StaticFileRoute(object):

    def __init__(self):
        self.method = 'GET'
        self.is_static = False
        self.route = re.compile('^/static/(.+)$')

    def match(self, url):
        if url.startswith('/static/'):
            return (url[1:], )
        return None

    def __call__(self, *args):
        fpath = os.path.join(ctx.application['document_root'], args[0])
        if not os.path.isfile(fpath):
            raise notfound()
        fext = os.path.splitext(fpath)[1]
        ctx.response.content_type = mimetypes.types_map.get(fext.lower(), 'application/octet-stream')
        return _static_file_generator(fpath)

def favicon_handler():
    return static_file_handler('/favicon.ico')

# 定义模版
def view(path):
    '''
    >>> @view('index.html')
    ... def test():
    ...     return dict(a=123,b=234)
    >>> t = test()
    >>> t.template_name
    'index.html'
    >>> t.model
    {'a': 123, 'b': 234}
    '''
    def _decorater(func):
        @functools.wraps(func)
        def _wrapper(*args, **kw):
            r = func(*args, **kw)
            if isinstance(r, dict):
                return Template(path, **r)
            raise ValueError('func result must be dict')
        return _wrapper
    return _decorater

_RE_INTERCEPTROR_STARTS_WITH = re.compile(r'^([^\*\?]+)\*?$')
_RE_INTERCEPTROR_ENDS_WITH = re.compile(r'^\*([^\*\?]+)$')

# 设置拦截器的匹配正则表达式
def _build_pattern_fn(pattern):
    m = _RE_INTERCEPTROR_STARTS_WITH.match(pattern)
    if m:
        return lambda p: p.startswith(m.group(1))
    m = _RE_INTERCEPTROR_ENDS_WITH.match(pattern)
    if m:
        return lambda p: p.endswith(m.group(1))
    raise ValueError('pattern define interceptor')

# 定义拦截器
def interceptor(pattern='/'):
    '''
    >>> @interceptor('*/api')
    ... def test():
    ...     return None
    >>> test.__interceptor__('hello/api')
    True
    >>> @interceptor('/api/*')
    ... def func():
    ...     return None
    >>> func.__interceptor__('/api/get/')
    True
    '''
    def _decorator(func):
        func.__interceptor__ = _build_pattern_fn(pattern)
        return func
    return _decorator

# 工具函数，匹配path时拦截器起作用
def _build_interceptor_fn(func, next):
    def _wrapper():
        if func.__interceptor__(ctx.request.path_info):
            return func(next)
        else:
            return next()
    return _wrapper

# 工具函数，遍历所有的拦截器，如果匹配到path就用拦截器包住
def _build_interceptor_chain(last_fn, *interceptor):
    '''
    >>> def target():
    ...     print 'test'
    ...     return 123
    >>> @interceptor('/')
    ... def f1(next):
    ...     print 'before f1'
    ...     try:
    ...         return next()
    ...     finally:
    ...         print 'after f1'
    >>> @interceptor('/api')
    ... def f2(next):
    ...     print 'before f2'
    ...     return next()
    >>> @interceptor('/')
    ... def f3(next):
    ...     print 'before f3'
    ...     try:
    ...         return next()
    ...     finally:
    ...         print 'after f3'
    >>> class Test(object):
    ...     path_info = '/api'
    >>> ctx.request = Test()
    >>> chain = _build_interceptor_chain(target, f1, f2, f3)
    >>> chain()
    before f1
    before f2
    before f3
    test
    after f3
    after f1
    123
    >>> class Test2(object):
    ...     path_info = '/test'
    >>> ctx.request = Test2()
    >>> chain = _build_interceptor_chain(target, f1, f2, f3)
    >>> chain()
    before f1
    before f3
    test
    after f3
    after f1
    123
    '''
    L = list(interceptor)
    L.reverse()
    fn = last_fn
    for f in L:
        fn = _build_interceptor_fn(f, fn)
    return fn

# 模版与model映射类
class Template(object):
    def __init__(self, template_name, **kw):
        self.template_name = template_name
        self.model = dict(**kw)

# 定义模版引擎
class TemplateEngine(object):
    def __call__(self, path, model):
        pass

# 缺省使用
class Jinja2TemplateEngine(TemplateEngine):
    def __init__(self, templ_dir, **kw):
        from jinja2 import Environment, FileSystemLoader
        self._env = Environment(loader=FileSystemLoader(templ_dir), **kw)

    def add_filter(self, name, fn_filter):
        self._env.filters[name] = fn_filter

    def __call__(self, path, model):
        return self._env.get_template(path).render(**model).encode('utf-8')

class WSGIApplication(object):
    def __init__(self, document_root=None, **kw):

        self._running = False

        self._document_root = document_root

        self._get_static = {}
        self._post_static = {}

        self._get_dynamic = []
        self._post_dynamic = []

        self._interceptors = []

    def _check_not_running(self):
        if self._running:
            raise RuntimeError("can't modify WSGIApplication when it is running")

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

    # 从模块添加url
    def add_model(self, mod):
        self._check_not_running()
        m = mod
        logging.info('add model %s' % mod.__name__)
        for name in dir(m):
            fn = getattr(m, name)
            if hasattr(fn, '__route__') and hasattr(fn, '__method__'):
                self.add_url(fn)

    # 添加一个Interceptor定义
    def add_interceptor(self, func):
        self._check_not_running()
        self._interceptors.append(func)
        logging.info('add interceptor %s ' % func.func_name)

    # 设置TemplateEngine
    @property
    def template_engine(self):
        self._template_engine

    @template_engine.setter
    def template_engine(self, engine):
        self._temlate_engine = engine

    # 返回WSGI处理函数
    def get_wsgi_application(self, debug=False):
        self._check_not_running()
        if debug:
            self._get_dynamic.append(StaticFileRoute())
        self._running = True

        _application = dict(document_root=self._document_root) # 这里只在取静态文件时有用，传入一个目录

        # 根据method与path路由获取处理函数，分为一般的和带参数的
        def fn_route():
            path = ctx.request.path_info
            method = ctx.request.method
            if method == 'GET':
                fn = self._get_static.get(path, None)
                if fn:
                    return fn()
                for fn in self._get_dynamic:
                    args = fn.match(path)
                    if args:
                        return fn(*args)
                raise notfound()
            if method == 'POST':
                fn = self._post_static.get(path, None)
                if fn:
                    return fn()
                for fn in self._post_dynamic:
                    args = fn.match(path)
                    if args:
                        return fn(*args)
                raise notfound()
            return badrequest()

        # 对于处理函数包裹上拦截器规则
        fn_exec = _build_interceptor_chain(fn_route, *self._interceptors)

        # WSGI入口处理函数
        def wsgi(env, start_response):
            ctx.application = _application
            ctx.request = Request(env)
            response = ctx.response = Response()
            try:
                r = fn_exec()
                if isinstance(r, Template):
                    r = self._temlate_engine(r.template_name, r.model)
                elif isinstance(r, unicode):
                    r = r.encode('utf-8')
                if r is None:
                    r = []
                start_response(response.status, response.headers)
                return r
            except RedirectError, e:
                response.set_header('Location', e.location)
                start_response(e.status, response.headers)
                return []
            except HttpError, e:
                start_response(e.status, response.headers)
                if e.status == '404 Not Found' and os.path.exists(r'templates/404.html'):
                    return self._temlate_engine('404.html', dict())
                return ['<html><body><h1>', e.status, '</h1></body></html>']
            except Exception, e:
                logging.exception(e)
                if not debug:
                    start_response('500 Internal Server Error', [])
                    return ['<html><body><h1>500 Internal Server Error</h1></body></html>']
                exc_type, exc_value, exc_traceback = sys.exc_info()
                fp = StringIO()
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=fp)
                stacks = fp.getvalue()
                fp.close()
                start_response('500 Internal Server Error', [])
                return [
                   r'''<html><body><h1>500 Internal Server Error</h1><div style="font-family:Monaco, Menlo, Consolas, 'Courier New', monospace;"><pre>''',
                    stacks.replace('<', '&lt;').replace('>', '&gt;'),
                    '</pre></div></body></html>']
            finally:
                del ctx.request
                del ctx.response
        return wsgi

    # 开发模式下直接启动服务器
    def run(self, port=9000, host='127.0.0.1'):
        from wsgiref.simple_server import make_server
        server = make_server(host, port, self.get_wsgi_application(debug=True))
        server.serve_forever()

'''
if __name__ == '__main__':
    wsgi.run()

else:
    application = wsgi.get_wsgi_application()
'''

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    import doctest
    doctest.testmod()
