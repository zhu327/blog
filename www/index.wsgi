import sae
import wsgiapp

application = sae.create_wsgi_app(wsgiapp.application)
