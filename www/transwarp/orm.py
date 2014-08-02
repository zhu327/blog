#!/usr/bin/env python
# -*- coding:utf-8 -*-

__author__ = 'zhu327'

'''
ORM 对象关系映射

from transwarp.orm import Model, StringField, IntegerField

class User(Mode):
    __table__ = 'user'
    id = IntegerField(primary_key=True)
    name = StringField()

# 直接通过类方法来查询
user = User.get('123')

# 创建实例:
user = User(id=123, name='Michael')
# 存入数据库:
user.insert()
'''

import db, logging

class Field(object):
    def __init__(self, **kw):
        self.name = kw.get('name', None)
        self._default = kw.get('default', None)
        self.primary_key = kw.get('primary_key', False)
        self.not_null = kw.get('not_null', False)
        self.updateable = kw.get('updateable', True)
        self.insertable = kw.get('insertable', True)
        self.datatype = kw.get('datatype', None)

    @property
    def default(self):
        d = self._default
        return d() if callable(d) else d

class IntegerField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'datatype' in kw:
            kw['datatype'] = 'bigint'
        super(IntegerField, self).__init__(**kw)

class StringField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'datatype' in kw:
            kw['datatype'] = 'varchar(255)'
        super(StringField, self).__init__(**kw)

# 基类，创建ORM映射
class ModelMetaClass(type):                                                                                                              
    def __new__(cls, clsname, bases, attrs):
        if clsname == 'Model':
            return super (ModelMetaClass, cls).__new__(cls, clsname, bases, attrs)
        mapping = {}
        primary_key = None
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                logging.info('mapping here %s, %s' % (k, v))
                if v.primary_key:
                    if not primary_key:
                        primary_key = k
                    else:
                        raise TypeError(r'primary key is already set %s, %s shuold be nomarl' % (primary_key, k))
                    if not v.not_null:
                        logging.warning(r"primary key can't null")
                        v.not_null = True
                    if v.insertable:
                        logging.warning(r"primary key can't update")
                        v.insertable = False
                if not v.name:
                    v.name = k
                mapping[k] = v
        if not primary_key:
            raise TypeError(r'there is no primary key')
        if not '__table__' in attrs:
            atter['__table__'] = clsname.lower()
        for k in mapping.iterkeys():
            attrs.pop(k)
        attrs['__mapping__'] = mapping
        attrs['__primary_key__'] = primary_key
        return super(ModelMetaClass, cls).__new__(cls, clsname, bases, attrs) 

class Model(dict):
    '''
    ORM CLASS

    >>> d = Model(id=123, name='Timmy')
    >>> d.id
    123
    >>> d.name
    'Timmy'
    >>> d.id=100
    >>> d.id
    100
    >>> d.h
    Traceback (most recent call last):
      ...
    AttributeError: dict obeject has no attr named h
    '''
    __metaclass__ = ModelMetaClass

    def __init__(self, **kw):
       super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'dict obeject has no attr named %s' % key)

    def __setattr__(self, key, value):
        self[key] = value 

    # 通过主键获取一行数据，返回对象
    @classmethod
    def get(cls, pk):
        l = db.select('select * form %s where %s=?' %  (cls.__table__, cls.__primary_key__,), pk)
        return cls(**l[0]) if l else None

    # 通过对象插入数据
    def insert(self):
        '''
        insert object to db

        >>> class User(Model):
        ...     __table__ = 'user'
        ...     id = IntegerField(primary_key=True)
        ...     name = StringField()
        >>> user1 = User(id=1, name='a')
        >>> user2 = User(id=2, name='b')
        >>> user1.insert()
        >>> user2.insert()
        >>> d = User.get(1)
        >>> d.id
        1
        >>> d.name
        u'a'
        '''
        params = {}
        for k, v in self.__mapping__.iteritems():
           if v.insertable:
               if v.name in self:
                   params[v.name] = self[k]
               else:
                   params[v.name] = v.default
        db.insert(self.__table__, **params)
        return self

if __name__ == '__main__':
    import doctest
    doctest.testmod()
