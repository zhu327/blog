# -*- coding: utf-8 -*-

from datetime import datetime
import markdown2

# 定义datetime_filter,输入是t，输出是unicode字符串
def datetime_filter(t):
    dt = datetime.fromtimestamp(t)
    return dt.strftime('%d %b %Y')

def rssdate_filter(t):
    dt = datetime.fromtimestamp(t)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")

def markdown_filter(content):
    return markdown2.markdown(content, extras=['fenced-code-blocks', 'code-color'])
