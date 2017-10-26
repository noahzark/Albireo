# from functools import wraps
from twisted.web import server, resource
from twisted.internet import reactor, endpoints
import json

rpc_exported_dict = {}


def rpc_export(f):
    func_name = f.__name__
    rpc_exported_dict[func_name] = f
    print func_name
    print rpc_exported_dict
    # @wraps(f)
    # def wrapper(*args, **kwargs):
    #     return f(*args, **kwargs)
    return f


class RPCInterface(resource.Resource):
    isLeaf = True

    def render_GET(self, request):
        rpc_method = request.path[1:]
        rpc_method_args = request.args
        if rpc_method in rpc_exported_dict:
            rpc_exported_dict[rpc_method](**rpc_method_args)
        else:
            print('no such a method ({0}) found'.format(rpc_method,))
        return ''


def setup_server():
    site = server.Site(RPCInterface())
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 8080)
    endpoint.listen(site)


@rpc_export
def user_favorite_update(user_id):
    print user_id
