from gevent import monkey
monkey.patch_all()

import sae
import wsgiapp

application = sae.create_wsgi_app(wsgiapp.application)
