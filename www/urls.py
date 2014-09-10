#!/usr/bin/env python
# -*- coding:utf-8 -*-

'''
MVC urls
'''

import re, hashlib, time, logging

from transwarp import db
from transwarp.web import get, post, view, interceptor, ctx, seeother, notfound
from models import User, Blog, Tag
from apis import api, APIError, APIValueError, Page
from config import configs

_COOKIE_NAME = 'bozsession'
_COOKIE_KEY = configs.get('session').get('secret')

def check_admin():
    user = ctx.request.user
    if user and user.admin:
        return
    raise APIError('Permission', 'user', 'no permission.')

def _get_blogs_by_page(page_index=1):
    total = Blog.count_all()
    page = Page(total, page_index)
    blogs = Blog.find_by('order by created desc limit ?,?', page.offset, page.limit)
    return blogs, page

def _get_blogs_by_tag(tag, page_index=1):
    total = Tag.count_by('where `name` = ?', tag)
    page = Page(total, int(page_index))
    blogs = Blog.find_by('where `id` in (select `blogid` from tag where `name` = ?) order by created desc limit ?,?', tag, page.offset, page.limit)
    return blogs, page

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
    blog = Blog.get(blog_id)
    if not blog:
        raise notfound()
    if blog.tags:
        blog.xtags = blog.tags.split(',')
    return dict(blog=blog)

@view('archives.html')
@get('/archives')
def archives():
    years = db.select('select distinct `year` from `blogs` order by created desc')
    if not years:
        raise notfound()
    xblogs = list()
    for y in years:
        blogs = Blog.find_by('where `year` = ? order by created desc', y.get('year'))
        xblogs.append(blogs)
    return dict(xblogs=xblogs)

@view('archives.html')
@get('/archives/:year')
def archives_year(year):
    blogs = Blog.find_by('where `year` = ? order by created desc', year)
    if not blogs:
        raise notfound()
    return dict(xblogs=[blogs])

@view('tags.html')
@get('/tags/:tag')
def tag(tag):
    blogs, page = _get_blogs_by_tag(tag)
    if not blogs:
        raise notfound()
    return dict(blogs=blogs, tag=tag, page=page)

@view('tags.html')
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
@get('/rss.xml')
def feed():
    blogs = Blog.find_by('order by created desc limit ?', 10)
    for blog in blogs:
        if blog.tags:
            blog.xtags = blog.tags.split(',')
    url = configs.get('blog_url')
    ctx.response.content_type = 'application/xml'
    return dict(blogs=blogs, url=url)

@view('signin.html')
@get('/signin')
def signin():
    return dict()

@api
@get('/api/users')
def api_get_users():
    total = User.count_all()
    page = Page(total, _get_page_index())
    users = User.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
    for u in users:
        u.password = '******'
    return dict(users=users, page=page)

_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')

@api
@post('/api/users')
def register_user():
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
    user = User.find_first('where email=?', email)
    if user:
        raise APIError('register:failed', 'email', 'Email is already in user')
    user = User(name=name, email=email, password=password, image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email).hexdigest())
    user.insert()
    return user

@view('register.html')
@get('/register')
def register():
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

# 计算加密算法cookie
def make_signed_cookie(id, password, max_age):
    expires = str(int(time.time()) + max_age)
    L = [id, expires, hashlib.md5('%s-%s-%s-%s' % (id, password, expires, _COOKIE_KEY)).hexdigest()]
    return '-'.join(L)

@interceptor('/')
def user_interceptor(next):
    user = None
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    if cookie:
        logging.info('REQUEST COOKIE: ' + cookie)
        user = parse_signed_cookie(cookie)
    ctx.request.user = user
    return next()

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

@api
@post('/api/blogs')
def api_create_blog():
    check_admin()
    i= ctx.request.input(name='', summary='', content='')
    name = i['name'].strip()
    summary = i['summary'].strip()
    content = i['content'].strip()
    if not name:
        raise APIValueError('name', 'name can not be empty.')
    if not summary:
        raise APIValueError('summary', 'summary can not be empty.')
    if not content:
        raise APIValueError('content', 'content can not be empty.')
    user = ctx.request.user
    blog = Blog(user_id=user.id, user_name=user.name, name=name, summary=summary, content=content)
    blog.insert()
    return blog

@api
@get('/api/blogs')
def api_get_blogs():
    blogs, page = _get_blogs_by_page()
    return dict(blogs=blogs, page=page)

@view('manage_blog_list.html')
@get('/manage/blogs')
def manage_blogs():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@interceptor('/manage/')
def manage_interceptor(next):
    user = ctx.request.user
    if user and user.admin:
        return next()
    raise seeother('/signin')

@api
@get('/api/blogs/:blog_id')
def api_modify_blog(blog_id):
    blog = Blog.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    return blog

@api
@post('/api/blogs/:blog_id')
def api_modify_blog(blog_id):
    check_admin()
    blog = Blog.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    i = ctx.request.input(name='', summary='', content='')
    name = i['name'].strip()
    summary = i['summary'].strip()
    content = i['content'].strip()
    if not name:
        raise APIValueError('name', 'name can not be empty.')
    if not summary:
        raise APIValueError('summary', 'summary can not be empty.')
    if not content:
        raise APIValueError('content', 'content can not be empty.')
    blog.name = name
    blog.summary = summary
    blog.content = content
    blog.update()
    return blog

@api
@post('/api/blogs/:blog_id/delete')
def api_delete_blog(blog_id):
    check_admin()
    blog = Blog.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    blog.delete()
    return dict(id=blog_id)

@api
@post('/api/blogs/:blog_id/comments')
def api_create_comments(blog_id):
    user = ctx.request.user
    if not user:
        raise APIValueError('user', 'need signin.')
    blog = Blog.get(blog_id)
    if not blog:
        raise APIValueError(blog_id, 'blog is not exist.')
    content = ctx.request.input(content='')['content'].strip()
    if not content:
        raise APIValueError('content')
    comment = Comment(blog_id=blog_id, user_id=user.id, user_name=user.name, user_image=user.image, content=content)
    comment.insert()
    return dict(comment=comment)

@api
@post('/api/comments/:comment_id/delete')
def api_delete_comment(comment_id):
    check_admin()
    comment = Comment.get(comment_id)
    if comment is None:
        raise APIResourceNotFoundError('Comment')
    comment.delete()
    return dict(id=comment_id)

@api
@get('/api/comments')
def api_get_comments():
    total = Comment.count_all()
    page = Page(total, _get_page_index())
    comments = Comment.find_by('order by created_at desc limit ?,?', page.offset, page.limit)
    return dict(comments=comments, page=page)

@get('/signout')
def signout():
    ctx.response.delete_cookie(_COOKIE_NAME)
    raise seeother('/')

@view('manage_bolg_edit.html')
@get('/manage/blogs/create')
def manage_blog_create():
    return dict(id=None, action='/api/blogs', redirect='/manage/blogs', user=ctx.request.user)

@view('manage_blog_edit.html')
@get('/manage/blogs/edit/:blog_id')
def manage_blog_modify(blog_id):
    blog = Blog.get(blog_id)
    if not blog:
        raise notfound()
    return dict(id=blog.id, name=blog.name, summary=blog.summary, content=blog.content, action='/api/blogs/%s' % blog_id, redirect='/manage/blogs', user=ctx.request.user)

@view('manage_user_list.html')
@get('/manage/users')
def manage_users():
    return dict(page_index=_get_page_index(), user=ctx.request.user)

@get('/manage/')
def manage_index():
    raise seeother('/manage/comments')

@view('manage_comment_list.html')
@get('/manage/comments')
def manage_comments():
    return dict(page_index=_get_page_index(), user=ctx.request.user)
