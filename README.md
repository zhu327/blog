### Boz

***

demo:<http://bozpy.sinaapp.com>

Boz是一个用Python实现的轻量级Blog程序。  
这是一个练习作品，开始于[廖雪峰的Python教程实战篇](http://www.liaoxuefeng.com/wiki/001374738125095c955c1e6d8bb493182103fac9270762a000/001397616003925a3d157284cd24bc0952d6c4a7c9d8c55000)。  
感谢廖雪峰提供的教程，让我从这个程序中收获良多。


Boz现有3个分支：

1. [awesome](https://github.com/zhu327/boz/tree/awesome)：廖雪峰教程的标准实现
2. master：主分支，运行于开发环境
3. [sae](https://github.com/zhu327/boz/tree/awesome): 部署在SAE(Sina App Engine)的master版本

master相对与awesome的改变主要是在前端的改变，前端可分为访客面与管理面，两面相对独立。  
访客面UI完全clone自[Heroic Yang's Blog](http://heroicyang.com/)；  
管理面UI由[Bootstrap](https://github.com/twbs/bootstrap/)简单的拼凑出来，界面简陋，实现了Blog后台管理基本功能。

开发环境：  
OSX, Python, MySQL, MySQLdb, Jinja2, markdown2

Boz设计模式：

1. 访客面 MVC
2. 管理面 MVVM

Boz实现了一个简单的Python Web框架，在www/transwarp目录下，包括对MySQLdb的封装，一个简单的ORM实现，以及一个WSGI的web框架实现。

数据库使用MySQL，模版引擎用到了Jinja2，使用markdown2来支持markdown格式。  
前端管理面用到了Bootstrap Jquery 以及MVVM库Vue.js。

部署：

1. MySQL中导入schema.sql
2. 修改config_override.py配置，可参考config_default.py
3. 修改template模版，包括blog名称，about页面信息
4. python wsgiapp.py即可运行，SAE分支还需要修改config.yaml相关信息
5. 后台/manage/默认用户名:admin@example.com 密码:123456，首次部署后需要到/manage/user修改密码
6. 日志评论使用[多说](http://duoshuo.com/)，需要把templates/blog.html下面的block comment修改为你自己的定制代码
   具体设置CSS[请看这里](http://heroicyang.com/2013/05/22/hexo-theme-modernist/)。

Boz是在业余学习的练习作品，前后学习编码差不多用了1个多月，学习了很多东西，准备输出学习笔记记录在<http://bozpy.sinaapp.com>上，各位看官如有兴趣，请订阅。

#### 小工具

通过文件发布文章，文件第一行为文章标题，第二行为标签，余下为正文.

[postEntry.py](https://gist.github.com/zhu327/2a473332a796146b4dbd)
