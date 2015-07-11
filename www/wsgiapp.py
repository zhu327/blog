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

import os, sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'site-packages.zip'))

import logging; logging.basicConfig(level=logging.INFO)

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs
from filters import datetime_filter, rssdate_filter, markdown_filter

# 初始化数据库
db.create_engine(**configs['db'])

# 创建一个WSGIApplication
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

# 初始化Jinja2模版引擎
template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# 把filter添加到jinja2，filter本身是一个函数对象
template_engine.add_filter('datetime', datetime_filter)
template_engine.add_filter('rssdate', rssdate_filter)
template_engine.add_filter('html', markdown_filter)

wsgi.template_engine = template_engine

# 加载url中的函数
import urls
wsgi.add_interceptor(urls.user_interceptor)
wsgi.add_interceptor(urls.manage_interceptor)
wsgi.add_model(urls)

# 在9000端口启动wsgi
if __name__ == '__main__':
    wsgi.run(9000)
else:
    application = wsgi.get_wsgi_application()
