# -*- coding:utf-8 -*-

import misaka as m
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from config import configs

# Create a custom renderer
class BleepRenderer(m.HtmlRenderer, m.SmartyPants):
    def block_code(self, text, lang):
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                text.strip()
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = HtmlFormatter()
        return highlight(text, lexer, formatter)


renderer = BleepRenderer()
md = m.Markdown(renderer,
    extensions=m.EXT_FENCED_CODE | m.EXT_NO_INTRA_EMPHASIS |
        m.EXT_AUTOLINK | m.EXT_LAX_HTML_BLOCKS | m.EXT_TABLES)


def get_summary(content):
    '''
    摘取markdown文章摘要
    '''
    size = configs.get('page').get('summary_size') - 1
    lines = []
    count = 0
    for i, line in enumerate(content.split('\n')):
        lines.append(line)
        count += line.count('```')
        if i >= size and (count % 2 == 0):
            break
    return  '\n'.join(lines)
