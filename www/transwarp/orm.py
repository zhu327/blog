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

    _order = 0

    def __init__(self, **kw):
        self.name = kw.get('name', None)
        self._default = kw.get('default', None)
        self.primary_key = kw.get('primary_key', False)
        self.nullable = kw.get('nullable', True)
        self.updateable = kw.get('updateable', True)
        self.insertable = kw.get('insertable', True)
        self.datatype = kw.get('datatype', None)
        self.auto_increment = kw.get('increment', False)
        Field._order = Field._order + 1

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

class FloatField(Field):

    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0.0
        if not 'datatype' in kw:
            kw['datatype'] = 'real'
        super(FloatField, self).__init__(**kw)

class BooleanField(Field):

    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = False
        if not 'datatype' in kw:
            kw['datatype'] = 'bool'
        super(BooleanField, self).__init__(**kw)

class TextField(Field):

    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'datatype' in kw:
            kw['datatype'] = 'text'
        super(TextField, self).__init__(**kw)

class BlobField(Field):

    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'datatype' in kw:
            kw['datatype'] = 'blob'
        super(BlobField, self).__init__(**kw)

class DatetimeField(Field):

    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'datatype' in kw:
            kw['datatype'] = 'datetime'
        super(DatetimeField, self).__init__(**kw)


class VersionField(Field):

    def __init__(self, name=None):
        super(VersionField, self).__init__(name=name, default=0, ddl='bigint')

def _gen_sql(table_name, mappings):
    pk = None
    sql = ['-- generating SQL for %s:' % table_name, 'create table `%s` (' % table_name]
    for v in sorted(mappings.values(), lambda x, y: cmp(x._order, y._order)):
        if not hasattr(v, 'datatype'):
            raise StandardError('no data type in field %s' % v)
        datatype = v.datatype
        nullable = v.nullable
        increment = v.auto_increment
        if v.primary_key:
            pk = v.name
        sql.append(nullable and '    `%s` %s,' % (v.name, datatype) or '    `%s` %s not null,' % (v.name, datatype))
        if increment:
            sql[-1] = sql[-1].rstrip(',') + ' auto_increment,'
    sql.append('    primary key(`%s`)' % pk)
    sql.append(');')
    return '\n'.join(sql)

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
                    if v.nullable:
                        logging.warning(r"primary key can't null")
                        v.nullable = False
                    if v.updateable:
                        logging.warning(r"primary key can't update")
                        v.updateable = False
                if not v.name:
                    v.name = k
                mapping[k] = v
        if not primary_key:
            raise TypeError(r'there is no primary key')
        if not '__table__' in attrs:
            attrs['__table__'] = clsname.lower()
        for k in mapping.iterkeys():
            attrs.pop(k)
        attrs['__mapping__'] = mapping
        attrs['__primary_key__'] = primary_key
        attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'], mapping)
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
        l = db.select('select * from `%s` where `%s`=?' %  (cls.__table__, cls.__primary_key__,), pk)
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
        {'name': 'a', 'id': 1}
        >>> user2.insert()
        {'name': 'b', 'id': 2}
        >>> d = User.get(1)
        >>> d.id
        1L
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

    def insert_id(self):
        params = {}
        for k, v in self.__mapping__.iteritems():
           if v.insertable:
               if v.name in self:
                   params[v.name] = self[k]
               else:
                   params[v.name] = v.default
        id = db.insert_id(self.__table__, **params)
        return id

    @classmethod
    def find_first(cls, where, *arg):
        l = db.select('select * from `%s` %s' % (cls.__table__, where), *arg)
        return cls(**l[0]) if l else None

    @classmethod
    def find_all(cls):
        '''
        >>> class User(Model):
        ...     __table__ = 'user'
        ...     id = IntegerField(primary_key=True)
        ...     name = StringField()
        >>> user5 = User(id=5, name='a')
        >>> user6 = User(id=6, name='b')
        >>> user5.insert()
        {'name': 'a', 'id': 5}
        >>> user6.insert()
        {'name': 'b', 'id': 6}
        >>> User.find_all()
        [{'id': 5L, 'name': u'a'}, {'id': 6L, 'name': u'b'}, {'id': 7L, 'name': u'a'}, {'id': 8L, 'name': u'a'}]
        '''
        l = db.select('select * from `%s`' % cls.__table__)
        return [cls(**x) for x in l]

    @classmethod
    def find_by(cls, where, *args):
        l = db.select('select * from `%s` %s' % (cls.__table__, where), *args)
        return [cls(**x) for x in l]

    @classmethod
    def count_all(cls):
        '''
        >>> class User(Model):
        ...     __table__ = 'user'
        ...     id = IntegerField(primary_key=True)
        ...     name = StringField()
        >>> user7 = User(id=7, name='a')
        >>> user8 = User(id=8, name='a')
        >>> user7.insert()
        {'name': 'a', 'id': 7}
        >>> user8.insert()
        {'name': 'a', 'id': 8}
        >>> User.count_all()
        2L
        '''
        return db.select_int('select count(`%s`) from `%s`' % (cls.__primary_key__, cls.__table__))

    @classmethod
    def count_by(cls, where, *args):
        return db.select_int('select count(`%s`) from `%s` %s' % (cls.__primary_key__, cls.__table__, where), *args)

    def update(self):
        '''
        update data

        >>> class User(Model):
        ...     __table__ = 'user'
        ...     id = IntegerField(primary_key=True)
        ...     name = StringField()
        >>> user1 = User.get(1)
        >>> user1.name = 'hello'
        >>> user1.update()
        {'id': 1L, 'name': 'hello'}
        >>> user1 = User.get(1)
        >>> user1.name
        u'hello'
        '''
        l = []
        args = []
        for k, v in self.__mapping__.iteritems():
            if v.updateable:
               l.append(v.name)
               args.append(getattr(self, k, v.default))
        l = ['`%s`=?' % x for x in l]
        args.append(getattr(self, self.__primary_key__))
        sql = 'update `%s` set %s where `%s`=?' % (self.__table__, ','.join(l), self.__mapping__[self.__primary_key__].name)
        db.execute(sql, *args)
        return self

    def delete(self):
        '''
        delete object form db

        >>> class User(Model):
        ...     __table__ = 'user'
        ...     id = IntegerField(primary_key=True)
        ...     name = StringField()
        >>> user3 = User(id=3, name='a')
        >>> user3.insert()
        {'name': 'a', 'id': 3}
        >>> d = User.get(3)
        >>> d
        {'id': 3L, 'name': u'a'}
        >>> d.delete()
        {'id': 3L, 'name': u'a'}
        >>> User.get(3) == None
        True
        '''
        sql = 'delete from `%s` where `%s`=?' % (self.__table__, self.__mapping__[self.__primary_key__].name)
        db.execute(sql, getattr(self, self.__primary_key__))
        return self

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db.create_engine('root', '', 'test')
    db.execute('drop table if exists user')
    db.execute('create table user (id int primary key, name varchar(255))')
    import doctest
    doctest.testmod()
