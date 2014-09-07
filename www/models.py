#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

'''
blogpy 数据库表定义
'''

import time

from transwarp.db import next_id
from transwarp.orm import Model, IntegerField, StringField, BooleanField, FloatField, TextField

class User(Model):
    __table__ = 'users'

    uid = StringField(primary_key=True, default=next_id, datatype='varchar(50)')
    email = StringField(updatable=False, datatype='varchar(50)')
    password = StringField(datatype='varchar(50)')
    admin = BooleanField()
    name = StringField(datatype='varchar(50)')
    created = FloatField(updatable=False, default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    bid = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    user_id = StringField(updatable=False, datatype='varchar(50)')
    user_name = StringField(datatype='varchar(50)')
    title = StringField(datatype='varchar(50)')
    content = TextField()
    tags = StringField(datatype='varchar(50)')
    created = FloatField(updatable=False, default=time.time)

class Tag(Model):
    __table__ = 'tag'

    tid = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    name = StringField(datatype='varchar(50)')

class TagMap(Model):
    __talbe__ = 'tagmap'

    id = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    tid = IntegerField(datatype='int(10)')
    bid = IntegerField(datatype='int(10)')
