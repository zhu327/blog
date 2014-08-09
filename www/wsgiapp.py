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
import os

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs

# 初始化数据库
db.create_engine(**configs['db'])

# 创建一个WSGIApplication
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))
# 初始化Jinja2模版引擎
template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

wsgi.template_engine = template_engine

# 加载url中的函数
import urls
wsgi.add_url(urls.test_users)

# 在9000端口启动wsgi
wsgi.run(9000)
