#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
保存了生成环境下的配置，设置的参数用覆盖标准环境下的配置
'''

import sae.const

configs = {
    'db': {
        'host': sae.const.MYSQL_HOST,
        'port': int(sae.const.MYSQL_PORT),
        'user': sae.const.MYSQL_USER,
        'passwd': sae.const.MYSQL_PASS,
        'db': sae.const.MYSQL_DB
    },
    'blog_url': 'bozpy.sinaapp.com'
}
