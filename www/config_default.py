#!/usr/bin/env python
# -*- coding:utf-8 -*_

'''
保存标准环境下的配置，生成环境的配置请修改config_override.py
'''

configs = {
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': '',
        'db': 'boz'
    },
    'session': {
        'secret': 'BlogZ'
    },
    'page': {
        'page_size': 5,
        'summary_size': 10,
        'list_size': 10
    },
    'blog_url': '127.0.0.1:9000'
}
