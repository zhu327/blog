#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
MVC urls
'''

import re, hashlib, time, logging

from transwarp.web import get, post, view, interceptor, ctx
from models import User, Blog, Comment
from apis import api, APIError, APIValueError
from config import configs

_COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.get('session').get('secret')

@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    user = User.find_first('where email=?', 'admin@example.com')
    return dict(user=user, blogs=blogs)

@api
@get('/api/users')
def api_get_users():
    users = User.find_all()
    # 消除密码
    for user in users:
        user['password'] = '******'

    return dict(users=users)

_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')

@api
@post('/api/users')
def register_user():
    i = ctx.request.input(name='', email='', password='')
    name = i['name'].strip()
    email = i['email'].strip().lower()
    password = i['password'].strip()
    if not name:
        raise APIValueError(name)
    if not email and not _RE_EMAIL.match(email):
        raise APIValueError(email)
    if not password and not _RE_MD5.match(password):
        raise APIValueError(password)
    user = User.find_first('where email=?', email)
    if user:
        raise APIError('register:failed', 'email', 'Email is already in user')
    user = User(name=name, email=email, password=password, image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email).hexdigest())
    user.insert()
    return user

@view('register.html')
@get('/register')
def register():
    return dict()

@api
@post('/api/authenticate')
def authenticate():
    i = ctx.request.input()
    email = i.get('email').strip().lower()
    password = i.get('password')
    user = User.find_first('where email=?', email)
    if not user:
        raise APIError('auth:failed', 'email', 'Invalid email')
    elif user.password != password:
        raise APIError('auth:failed', 'password', 'Invalid password')
    max_age = 604800
    cookie = make_signed_cookie(user.id, user.password, max_age)
    ctx.response.set_cookie(_COOKIE_NAME, cookie, max_age=max_age)
    user.password = '******'
    return user

# 计算加密算法cookie
def make_signed_cookie(id, password, max_age):
    expires = str(int(time.time()) + max_age)
    L = [id, expires, hashlib.md5('%s-%s-%s-%s' % (id, password, expires, _COOKIE_KEY)).hexdigest()]
    return '-'.join(L)

@interceptor('/')
def user_interceptor(next):
    user = None
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    if cookie:
        user = parse_signed_cookie(cookie)
    ctx.request.user = user
    return next()

# 解密cookie
def parse_signed_cookie(cookie):
    try:
        L = cookie.split('-')
        if len(L) != 3:
            return None
        id, expries, md5 = L
        if int(expries) < time.time():
            return None
        user = User.get(id)
        if not user:
            return None
        if md5 != hashlib.md5('%s-%s-%s-%s' % (id, User.password, expires, _COOKIE_KEY)).hexdigest():
            return None
        return user
    except:
        return None
