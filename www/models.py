#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

'''
blogpy 数据库表定义
'''

import time
from datetime import datetime

from transwarp.orm import Model, IntegerField, StringField, FloatField, TextField

class User(Model):
    __table__ = 'user'

    id = StringField(primary_key=True, datatype='varchar(50)')
    email = StringField(datatype='varchar(50)')
    password = StringField(datatype='varchar(50)')
    name = StringField(datatype='varchar(50)')

class Blogs(Model):
    __table__ = 'blogs'

    id = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    title = StringField(datatype='varchar(50)')
    summary = TextField(datatype='mediumtext')
    content = TextField()
    tags = StringField(datatype='varchar(50)')
    created = FloatField(updateable=False, default=time.time)
    year = IntegerField(datatype='int(5)', updateable=False, default=datetime.now().year)

class Tags(Model):
    __table__ = 'tags'

    id = IntegerField(primary_key=True, increment=True, datatype='int(10)')
    tag = StringField(datatype='varchar(50)')
    blog = IntegerField(datatype='int(10)')
