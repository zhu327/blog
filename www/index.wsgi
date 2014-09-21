import sae
import wsgiapp

from gevent import monkey
monkey.patch_all()

application = sae.create_wsgi_app(wsgiapp.application)
