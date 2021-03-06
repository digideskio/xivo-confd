# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Avencall
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

import logging
import xivo_dao

from functools import partial

from xivo.consul_helpers import ServiceCatalogRegistration
from xivo_confd import setup_app
from xivo_confd.server import run_server

from .service_discovery import self_check

logger = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, config):
        self.config = config

    def run(self):
        logger.debug('xivo-confd running...')

        xivo_dao.init_db_from_config(self.config)

        app = setup_app(self.config)

        with ServiceCatalogRegistration('xivo-confd',
                                        self.config['uuid'],
                                        self.config['consul'],
                                        self.config['service_discovery'],
                                        self.config['bus'],
                                        partial(self_check, self.config)):
            run_server(app)
