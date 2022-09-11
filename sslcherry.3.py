from __future__ import division

"""HTTPS servers for CherryPy using the M2Crypto package"""

import M2Crypto.SSL
from cherrypy import _cphttpserver, _cputil
import cherrypy
import SocketServer, BaseHTTPServer
import traceback, sys


class SslCherryConnection(M2Crypto.SSL.Connection):
    def __init__(self, socket):
        """Create an M2Crypto.SSL.Connection using the key file specified in the config"""

        context = M2Crypto.SSL.Context()
        context.load_cert(cpg.configOption.sslKeyFile)
        M2Crypto.SSL.Connection.__init__(self, context, socket)

        self._cpLogMessage = _cputil.getSpecialFunction('_cpLogMessage')

    def settimeout(self, timeout):
        """Add settimeout method, which is missing M2Crypto.SSL.Connection"""

        self.socket.settimeout(timeout)

    def accept(self):
        while 1:
            try:
                return M2Crypto.SSL.Connection.accept(self)
            except M2Crypto.SSL.SSLError, e:
                self._cpLogMessage('m2crypto ssl exception "%s"' % str(e), 'SSL', 1)


class SslCherryServer(_cphttpserver.CherryHTTPServer):
    """Single threaded HTTPS server"""

    def server_bind(self):
        """Wrap the socket with a SslCherryConnection object before proceeding as normal"""

        self.socket = SslCherryConnection(self.socket)
        _cphttpserver.CherryHTTPServer.server_bind(self)


class SslCherryPooledThreadServer(_cphttpserver.PooledThreadServer):
    """Thread pooled HTTPS server"""

    def server_bind(self):
        """Wrap the socket with a SslCherryConnection object before proceeding as normal"""

        self.socket = SslCherryConnection(self.socket)
        _cphttpserver.PooledThreadServer.server_bind(self)


def start(configFile=None, parsedConfigFile=None, configDict={}):
    """Start an HTTPS server instead of an HTTP server"""

    # Initialise config
    cherrypy.server.start(configFile, parsedConfigFile, configDict, True)

    MyCherryHTTPServer = SslCherryServer

    MyCherryHTTPServer.request_queue_size = cpg.configOption.socketQueueSize

    _cphttpserver.CherryHTTPRequestHandler.protocol_version = cpg.configOption.protocolVersion

    _cphttpserver.run_server(_cphttpserver.CherryHTTPRequestHandler, MyCherryHTTPServer,
                             (cpg.configOption.socketHost, cpg.configOption.socketPort),
                             cpg.configOption.socketFile)
