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
import os, time
from datetime import datetime

from transwarp import db, markdown2
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs

# 初始化数据库
db.create_engine(**configs['db'])

# 创建一个WSGIApplication
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

# 定义datetime_filter,输入是t，输出是unicode字符串
def datetime_filter(t):
    dt = datetime.fromtimestamp(t)
    return dt.strftime('%b %d %Y')

def date_filter(t):
    dt = datetime.fromtimestamp(t)
    return dt.strftime('%b %d')

def rssdate_filter(t):
    dt = datetime.fromtimestamp(t)
    return dt.isoformat()

def markdown_filter(content):
    return markdown2.markdown(content)

# 初始化Jinja2模版引擎
template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# 把filter添加到jinja2，filter本身是一个函数对象
template_engine.add_filter('datetime', datetime_filter)
template_engine.add_filter('date', date_filter)
template_engine.add_filter('rssdate', rssdate_filter)
template_engine.add_filter('html', markdown_filter)

wsgi.template_engine = template_engine

# 加载url中的函数
import urls
wsgi.add_model(urls)
wsgi.add_interceptor(urls.user_interceptor)
wsgi.add_interceptor(urls.manage_interceptor)

# 在9000端口启动wsgi
wsgi.run(9000)
