#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'zhu327'

from models import User, Blog, Comment

from transwarp import db

db.create_engine('root', '', 'blogpy')

u = User(name='Test', email='test@example.com', password='1234567890', image='about:blank')

u.insert()

u1 = User.find_first('where email=?', 'test@example.com')
print 'find user\'s name:', u1.name
u1.delete()

u2 = User.find_first('where email=?', 'test@example.com')
print 'find user:', u2

