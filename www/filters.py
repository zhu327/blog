# -*- coding: utf-8 -*-

from utils import md

# 定义datetime_filter,输入是t，输出是unicode字符串
def datetime_filter(t):
    return t.strftime('%d %b %Y')

def rssdate_filter(t):
    return t.strftime("%a, %d %b %Y %H:%M:%S %z")

def markdown_filter(content):
    return md.render(content)
