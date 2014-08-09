#!/usr/bin/env python
# -*- coding:utf-8 -*-

import config_default

configs = config_default.configs

# 瀛楀吀鍚堝苟
def merge(default, override):
    r = {}
    for k, v in default.iteritems():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass
