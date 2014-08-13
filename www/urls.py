#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
MVC urls
'''

from transwarp.web import get, view
from models import User, Blog, Comment

@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    # 查找登陆用户
    user = User.find_first('where email=?', 'admin@example.com')
    return dict(user=user, blogs=blogs)
