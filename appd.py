from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor
from server import app

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
