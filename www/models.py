#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

'''
blogpy 数据库表定义
'''

import time

from transwarp.db import next_id
from transwarp.orm import Model, StringField, BooleanField, FloatField, TextField

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, datatype='varchar(50)')
    email = StringField(updatable=False, datatype='varchar(50)')
    password = StringField(datatype='varchar(50)')
    admin = BooleanField()
    name = StringField(datatype='varchar(50)')
    image = StringField(datatype='varchar(500)')
    created_at = FloatField(updatable=False, default=time.time)

class Blog(Model):
     __table__ = 'blogs'

     id = StringField(primary_key=True, default=next_id, datatype='varchar(50)')
     user_id = StringField(updatable=False, datatype='varchar(50)')
     user_name = StringField(datatype='varchar(50)')
     user_image = StringField(datatype='varchar(500)')
     name = StringField(datatype='varchar(50)')
     summary = StringField(datatype='varchar(200)')
     content = TextField()
     created_at = FloatField(updatable=False, default=time.time)

class Comment(Model):
     __table__ = 'comments'

     id = StringField(primary_key=True, default=next_id, datatype='varchar(50)')
     blog_id = StringField(updatable=False, datatype='varchar(50)')
     user_id = StringField(updatable=False, datatype='varchar(50)')
     user_name = StringField(datatype='varchar(50)')
     user_image = StringField(datatype='varchar(500)')
     content = TextField()
     created_at = FloatField(updatable=False, default=time.time)
