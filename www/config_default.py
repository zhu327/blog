#!/usr/bin/env python
# -*- coding:utf-8 -*_

'''
保存标准环境下的配置，生成环境的配置请修改config_override.py
'''

configs = {
    'db': {
        'host': '127.0.0.1',
        'user': 'root',
        'passwd': '',
        'db': 'blogpy'
    },
    'session': {
        'secret': 'BlogPy'
    }
}
