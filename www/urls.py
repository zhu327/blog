#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
MVC urls
'''

from transwarp.web import get, view
from models import User, Blog, Comment
from apis import api

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
        user['password'] = '********'

    return dict(users=users)
