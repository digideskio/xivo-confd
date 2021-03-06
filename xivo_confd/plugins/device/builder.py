# -*- coding: utf-8 -*-

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

from xivo_confd import bus

from xivo_confd.database import device as device_db

from xivo_confd.plugins.device.service import (DeviceService,
                                               SearchEngine)

from xivo_confd.plugins.device.update import (DeviceUpdater,
                                              ProvdUpdater)

from xivo_confd.plugins.device.generators import (ConfigGenerator,
                                                  UserGenerator,
                                                  ExtensionGenerator,
                                                  RawConfigGenerator,
                                                  FuncKeyGenerator,
                                                  SipGenerator,
                                                  SccpGenerator)

from xivo_confd.plugins.device.dao import DeviceDao
from xivo_confd.plugins.device.notifier import DeviceNotifier
from xivo_confd.plugins.device.validator import build_validator

from xivo_confd.plugins.device.funckey import build_converters

from xivo_dao.resources.line import dao as line_dao
from xivo_dao.resources.user_line import dao as user_line_dao
from xivo_dao.resources.line_extension import dao as line_extension_dao
from xivo_dao.resources.user import dao as user_dao
from xivo_dao.resources.func_key_template import dao as template_dao
from xivo_dao.resources.extension import dao as extension_dao


def build_dao(provd_client):
    return DeviceDao(provd_client)


def build_service(device_dao):
    search_engine = SearchEngine(device_dao)
    device_validator = build_validator(device_dao, line_dao)
    device_notifier = DeviceNotifier(bus)
    device_service = DeviceService(device_dao,
                                   device_validator,
                                   device_notifier,
                                   search_engine,
                                   line_dao)

    return device_service


def build_device_updater(provd_client):
    device_dao = build_dao(provd_client)
    generator = build_generators(device_dao)
    provd_updater = ProvdUpdater(device_dao, generator, line_dao)
    return DeviceUpdater(user_dao,
                         line_dao,
                         user_line_dao,
                         line_extension_dao,
                         provd_updater)


def build_generators(device_dao):
    converters = build_converters()
    funckey_generator = FuncKeyGenerator(user_dao,
                                         line_dao,
                                         user_line_dao,
                                         template_dao,
                                         device_dao,
                                         converters)

    sip_generator = SipGenerator(device_dao,
                                 device_db)

    sccp_generator = SccpGenerator(device_dao,
                                   line_dao)

    user_generator = UserGenerator(device_db)

    extension_generator = ExtensionGenerator(extension_dao)

    raw_config_generator = RawConfigGenerator([user_generator,
                                               extension_generator,
                                               funckey_generator,
                                               sip_generator,
                                               sccp_generator])

    config_generator = ConfigGenerator(raw_config_generator)

    return config_generator
