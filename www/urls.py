#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
MVC urls
'''

import re, hashlib, time
from collections import OrderedDict

from utils import md, get_summary
from transwarp import db
from transwarp.web import get, post, view, interceptor, ctx, seeother, notfound
from models import User, Blogs, Tags
from apis import api, APIError, APIValueError, Page
from config import configs

_COOKIE_NAME = 'bozsession'
_COOKIE_KEY = configs.get('session').get('secret')

def _get_page_index():
    page_index = 1
    try:
        page_index = int(ctx.request.get('page', '1'))
    except ValueError:
        pass
    return page_index

def _get_blogs_by_page(page_index=1, page_size=None):
    total = Blogs.count_all()
    if page_size:
        page = Page(total, page_index, page_size=page_size)
    else:
        page = Page(total, page_index)
    blogs = Blogs.find_by('order by created desc limit ?,?', page.offset, page.limit)
    return blogs, page

def _get_blogs_by_tag(tag, page_index=1):
    total = Tags.count_by('where `tag` = ?', tag)
    page = Page(total, int(page_index))
    sql = 'SELECT `blogs`.* FROM `blogs` LEFT JOIN `tags` ON `tags`.`blog` = `blogs`.`id` WHERE `tags`.`tag` = ? ORDER BY `created` DESC limit ?,? '
    blogs = db.select(sql, tag, page.offset, page.limit)
    return blogs, page

def _get_summary(content):
    return md.render(get_summary(content))

def check_admin():
    user = ctx.request.user
    if user:
        return
    raise APIError('Permission', 'user', 'no permission.')

# 计算加密算法cookie
def make_signed_cookie(id, password, max_age):
    expires = str(int(time.time()) + max_age)
    L = [id, expires, hashlib.md5('%s-%s-%s-%s' % (id, password, expires, _COOKIE_KEY)).hexdigest()]
    return '-'.join(L)

# 解密cookie
def parse_signed_cookie(cookie):
    try:
        L = cookie.split('-')
        if len(L) != 3:
            return None
        id, expires, md5 = L
        if int(expires) < time.time():
            return None
        user = User.get(id)
        if not user:
            return None
        if md5 != hashlib.md5('%s-%s-%s-%s' % (id, user.password, expires, _COOKIE_KEY)).hexdigest():
            return None
        return user
    except:
        return None

@interceptor('/')
def user_interceptor(next):
    user = None
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    if cookie:
        user = parse_signed_cookie(cookie)
    ctx.request.user = user
    return next()

@interceptor('/manage/')
def manage_interceptor(next):
    user = ctx.request.user
    if user:
        return next()
    raise seeother('/signin')

@view('blogs.html')
@get('/')
def index():
    blogs, page = _get_blogs_by_page()
    return dict(blogs=blogs, page=page)

@view('blogs.html')
@get('/page/:page_index')
def page(page_index):
    blogs, page = _get_blogs_by_page(int(page_index))
    if not blogs:
        raise notfound()
    return dict(blogs=blogs, page=page)

@view('blog.html')
@get('/blog/:blog_id')
def blog(blog_id):
    blog = Blogs.get(blog_id)
    if not blog:
        raise notfound()
    if blog.tags:
        blog.xtags = blog.tags.split(',')
    rps = Blogs.find_by('order by created desc limit ?', 3)
    return dict(blog=blog, rps=rps)

@view('archives.html')
@get('/archives')
def archives():
    sql = 'SELECT YEAR(`created`) AS `year`, `id`, `title`, `created` FROM `blogs` ORDER BY `created` DESC'
    blogs = db.select(sql)
    if not blogs:
        raise notfound()
    xblogs = OrderedDict()
    for blog in blogs:
        if not blog['year'] in xblogs:
            xblogs[blog['year']] = [blog]
        else:
            xblogs[blog['year']].append(blog)
    return dict(xblogs=xblogs)

@view('tags.html')
@get('/tags')
def tags():
    tags = db.select('SELECT COUNT(`id`) AS `count`, `tag` from tags GROUP BY `tag` ORDER BY `count` DESC')
    return dict(tags=tags)

@view('tag.html')
@get('/tags/:tag')
def tag(tag):
    blogs, page = _get_blogs_by_tag(tag)
    if not blogs:
        raise notfound()
    return dict(blogs=blogs, tag=tag, page=page)

@view('tag.html')
@get('/tags/:tag/:page_index')
def tag_page(tag, page_index):
    blogs, page = _get_blogs_by_tag(tag, page_index)
    if not blogs:
        raise notfound()
    return dict(blogs=blogs, tag=tag, page=page)

@view('about.html')
@get('/about')
def about():
    return dict()

@view('rss.xml')
@get('/feed')
def feed():
    blogs = Blogs.find_by('order by created desc limit ?', 10)
    for blog in blogs:
        if blog.tags:
            blog.xtags = blog.tags.split(',')
    url = configs.get('blog_url')
    user = User.find_first('')
    ctx.response.content_type = 'application/xml'
    return dict(blogs=blogs, url=url, user=user)

@view('sitemap.xml')
@get('/sitemap.xml')
def sitemap():
    blogs = db.select('select `id` from `blogs` order by `created` desc limit ?', 100)
    url = configs.get('blog_url')
    ctx.response.content_type = 'application/xml'
    return dict(blogs=blogs, url=url)

@view('signin.html')
@get('/signin')
def signin():
    return dict()

@api
@post('/api/authenticate')
def authenticate():
    i = ctx.request.input()
    email = i.get('email').strip().lower()
    password = i.get('password')
    user = User.find_first('where email=?', email)
    if not user:
        raise APIError('auth:failed', 'email', 'Invalid email')
    elif user.password != password:
        raise APIError('auth:failed', 'password', 'Invalid password')
    max_age = 604800
    cookie = make_signed_cookie(user.id, user.password, max_age)
    ctx.response.set_cookie(_COOKIE_NAME, cookie, max_age=max_age)
    user.password = '******'
    return user

@view('manage_blog_edit.html')
@get('/manage/blogs/create')
def manage_blog_create():
    return dict(id=None, action='/api/blogs', redirect='/manage/blogs')

@api
@post('/api/blogs')
def api_create_blog():
    check_admin()
    i= ctx.request.input(title='', tags='', content='')
    title = i['title'].strip()
    tags = i['tags'].strip()
    content = i['content'].strip()
    if not title:
        raise APIValueError('title', 'title can not be empty.')
    if not content:
        raise APIValueError('content', 'content can not be empty.')
    summary = _get_summary(content)
    blog = Blogs(title=title, tags=tags, summary=summary, content=content)
    id = blog.insert_id()
    tags = tags.split(',')
    if tags:
        sql = "INSERT INTO `tags` (`tag`, `blog`) VALUES {}".format(', '.join(map(
            lambda x: "('{}', '{}')".format(x, id), tags
        )))
        db.execute(sql)
    return dict(id=id)

@view('manage_blog_edit.html')
@get('/manage/blogs/edit/:blog_id')
def manage_blog_modify(blog_id):
    blog = Blogs.get(blog_id)
    if not blog:
        raise notfound()
    return dict(id=blog.id, action='/api/blogs/%s' % blog_id, redirect='/manage/blogs')

@api
@post('/api/blogs/:blog_id')
def api_modify_blog(blog_id):
    check_admin()
    blog = Blogs.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    i= ctx.request.input(title='', tags='', content='')
    title = i['title'].strip()
    tags = i['tags'].strip()
    content = i['content'].strip()
    if not title:
        raise APIValueError('title', 'title can not be empty.')
    if not content:
        raise APIValueError('content', 'content can not be empty.')
    summary = _get_summary(content)
    blog.title = title
    blog.summary = summary
    blog.content = content
    blog.tags = tags
    blog.update()
    db.execute('delete from `tags` where `blog`=?', blog_id)
    tags = tags.split(',')
    if tags:
        sql = "INSERT INTO `tags` (`tag`, `blog`) VALUES {}".format(', '.join(map(
            lambda x: "('{}', '{}')".format(x, blog_id), tags
        )))
        db.execute(sql)
    return dict(id=blog_id)

@api
@get('/api/blogs/:blog_id')
def api_get_blog(blog_id):
    blog = Blogs.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    return blog

@get('/signout')
def signout():
    ctx.response.delete_cookie(_COOKIE_NAME)
    raise seeother('/')

@view('manage_blog_list.html')
@get('/manage/blogs')
def manage_blogs():
    return dict(page_index=_get_page_index())

@api
@get('/api/blogs')
def api_get_blogs():
    blogs, page = _get_blogs_by_page(_get_page_index(), configs.get('page').get('list_size'))
    return dict(blogs=blogs, page=page)

@view('/manage_user.html')
@get('/manage/user')
def manage_user():
    return dict()

@api
@get('/api/user')
def api_get_user():
    user = User.find_first('')
    user.password = '******'
    return user

_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')

@api
@post('/api/user')
def register_user():
    check_admin()
    i = ctx.request.input(name='', email='', password='')
    name = i['name'].strip()
    email = i['email'].strip().lower()
    password = i['password'].strip()
    if not name:
        raise APIValueError(name)
    if not email and not _RE_EMAIL.match(email):
        raise APIValueError(email)
    if not password and not _RE_MD5.match(password):
        raise APIValueError(password)
    user = User.find_first('')
    user.name = name
    user.email=email
    user.password=password
    user.update()
    user.password = '******'
    return user

@api
@post('/api/blogs/:blog_id/delete')
def api_delete_blog(blog_id):
    check_admin()
    blog = Blogs.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    blog.delete()
    db.execute('delete from `tags` where `blog`=?', blog_id)
    return dict(id=blog_id)

@get('/manage/')
def manage_index():
    raise seeother('/manage/blogs')
