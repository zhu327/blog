#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

'''
blogpy 数据库表定义
'''

import time
from datetime import datetime

from transwarp.db import next_id
from transwarp.orm import Model, IntegerField, StringField, BooleanField, FloatField, TextField

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, datatype='varchar(50)')
    email = StringField(updatable=False, datatype='varchar(50)')
    password = StringField(datatype='varchar(50)')
    admin = BooleanField()
    name = StringField(datatype='varchar(50)')
    created = FloatField(updatable=False, default=time.time)

class Blog(Model):
    __table__ = 'blogs'

    id = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    user_id = StringField(updatable=False, datatype='varchar(50)')
    user_name = StringField(datatype='varchar(50)')
    title = StringField(datatype='varchar(50)')
    summary = TextField(datatype='mediumtext')
    content = TextField()
    tags = StringField(datatype='varchar(50)')
    created = FloatField(updatable=False, default=time.time)
    year = IntegerField(datatype='int(5)', default=datetime.now().year)

class Tag(Model):
    __table__ = 'tag'

    id = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    name = StringField(datatype='varchar(50)')
    blogid = IntegerField(datatype='int(10)')
