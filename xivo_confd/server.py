# -*- coding: utf-8 -*-

# Copyright (C) 2016 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import signal
import logging
import cherrypy

from cherrypy import wsgiserver
from cherrypy.process.servers import ServerAdapter
from cherrypy.wsgiserver import CherryPyWSGIServer
from werkzeug.contrib.profiler import ProfilerMiddleware
from xivo import http_helpers

logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    cherrypy.engine.exit()


def run_server(app):
    http_config = app.config['rest_api']['http']
    https_config = app.config['rest_api']['https']

    signal.signal(signal.SIGTERM, signal_handler)
    if app.config['profile']:
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                          profile_dir=app.config['profile'])

    wsgi_app = wsgiserver.WSGIPathInfoDispatcher({'/': app})

    cherrypy.server.unsubscribe()
    cherrypy.config.update({'environment': 'production'})

    if not (http_config['enabled'] or https_config['enabled']):
        logger.critical('No HTTP/HTTPS server enabled')
        exit()

    if https_config['enabled']:
        try:
            bind_addr_https = (https_config['listen'], https_config['port'])
            server_https = CherryPyWSGIServer(bind_addr=bind_addr_https,
                                              wsgi_app=wsgi_app)
            server_https.ssl_adapter = http_helpers.ssl_adapter(https_config['certificate'],
                                                                https_config['private_key'],
                                                                https_config['ciphers'])
            ServerAdapter(cherrypy.engine, server_https).subscribe()

            logger.debug('HTTPS server starting on %s:%s', *bind_addr_https)

        except IOError as e:
            logger.warning("HTTPS server won't start: %s", e)
    else:
        logger.debug('HTTPS server is disabled')

    if http_config['enabled']:
        bind_addr_http = (http_config['listen'], http_config['port'])
        server_http = CherryPyWSGIServer(bind_addr=bind_addr_http,
                                         wsgi_app=wsgi_app)
        ServerAdapter(cherrypy.engine, server_http).subscribe()

        logger.debug('HTTP server starting on %s:%s', *bind_addr_http)
    else:
        logger.debug('HTTP server is disabled')

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        cherrypy.engine.stop()
