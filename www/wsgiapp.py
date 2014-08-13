#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
WSGIApplication 运行步骤
1.创建数据库引擎
2.创建wsgi
3.创建模版引擎
4.注册模版引擎到wsgi
5.wsgi注册urls路由
6.运行wsgi
'''

import logging; logging.basicConfig(level=logging.INFO)
import os, time, datetime

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs

# 初始化数据库
db.create_engine(**configs['db'])

# 创建一个WSGIApplication
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

# 定义datetime_filter,输入是t，输出是unicode字符串
def datetime_filter(t):
    delta = int(time.time()-t)
    if delta < 60:
        return u'1分组前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.moth, dt.day)

# 初始化Jinja2模版引擎
template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# 把filter添加到jinja2，filter本身是一个函数对象
template_engine.add_filter('datetime', datetime_filter)

wsgi.template_engine = template_engine

# 加载url中的函数
import urls
wsgi.add_model(urls)

# 在9000端口启动wsgi
wsgi.run(9000)
