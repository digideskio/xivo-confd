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

from xivo_confd.helpers.resource import CRUDService
from xivo_confd.plugins.device.model import LineSIPConverter, LineSCCPConverter

from xivo_dao.resources.utils.search import SearchResult
from xivo_dao.helpers import errors


class DeviceService(CRUDService):

    def __init__(self, dao, validator, notifier, search_engine, line_dao):
        super(DeviceService, self).__init__(dao, validator, notifier)
        self.search_engine = search_engine
        self.line_dao = line_dao

    def search(self, parameters):
        return self.search_engine.search(parameters)

    def synchronize(self, device):
        self.dao.synchronize(device)

    def reset_autoprov(self, device):
        self.dao.reset_autoprov(device)
        self.reset_line(device)

    def reset_line(self, device):
        line = self.line_dao.find_by(device=device.id)
        if line:
            line.device_id = None
            self.line_dao.edit(line)


class LineDeviceAssociationService(object):

    def __init__(self, line_dao, device_updater):
        self.line_dao = line_dao
        self.device_updater = device_updater

    def get_line(self, line_id):
        return self.line_dao.get(line_id)

    def associate(self, line, device):
        line.device_id = device.id
        self.line_dao.edit(line)
        self.device_updater.update_for_line(line)

    def dissociate(self, line, device):
        line.device_id = None
        self.line_dao.edit(line)
        self.device_updater.update_for_line(line)


class DeviceUpdater(object):

    def __init__(self, line_updater, funckey_updater, user_dao, line_dao, user_line_dao, line_extension_dao, device_dao):
        self.line_updater = line_updater
        self.funckey_updater = funckey_updater
        self.user_dao = user_dao
        self.line_dao = line_dao
        self.user_line_dao = user_line_dao
        self.line_extension_dao = line_extension_dao
        self.device_dao = device_dao

    def update_for_template(self, template):
        private_users = self.user_dao.find_all_by(func_key_private_template_id=template.id)
        public_users = self.user_dao.find_all_by(func_key_template_id=template.id)
        for user in private_users + public_users:
            self.update_for_user(user)

    def update_for_extension(self, extension):
        line_extensions = self.line_extension_dao.find_all_by(extension_id=extension.id)
        for line_extension in line_extensions:
            line = self.line_dao.get(line_extension.line_id)
            self.update_for_line(line)

    def update_for_user(self, user):
        for user_line in self.user_line_dao.find_all_by_user_id(user.id):
            line = self.line_dao.get(user_line.line_id)
            self.update_for_line(line)

    def update_for_line(self, line):
        device_id = getattr(line, 'device_id', None)
        if device_id:
            device = self.device_dao.get(device_id)
            self.update_device(device)

    def update_for_endpoint_sip(self, sip):
        line = self.line_dao.find_by(protocol='sip', protocolid=sip.id)
        if line:
            self.update_for_line(line)

    def update_device(self, device):
        self.line_updater.update(device)
        self.funckey_updater.update(device)


class FuncKeyDeviceUpdater(object):

    def __init__(self, user_dao, line_dao, user_line_dao, template_dao, device_dao, converters):
        self.user_dao = user_dao
        self.line_dao = line_dao
        self.user_line_dao = user_line_dao
        self.device_dao = device_dao
        self.template_dao = template_dao
        self.converters = converters

    def update(self, device):
        for user, line in self.user_line_pairs_for_device(device):
            template = self.get_unified_template(user)
            funckeys = self.convert_funckeys(user, line, template)
            self.device_dao.update_funckeys(device, funckeys)

    def user_line_pairs_for_device(self, device):
        lines = self.line_dao.find_all_by(device=device.id)
        for line in lines:
            main_user_line = self.user_line_dao.find_main_user_line(line.id)
            if main_user_line:
                user = self.user_dao.get(main_user_line.user_id)
                yield user, line

    def get_unified_template(self, user):
        private_template = self.template_dao.get(user.private_template_id)
        if user.func_key_template_id:
            public_template = self.template_dao.get(user.func_key_template_id)
            return public_template.merge(private_template)
        return private_template

    def convert_funckeys(self, user, line, template):
        funckeys = {}
        for pos, funckey in template.keys.iteritems():
            converter = self.converters[funckey.destination.type]
            funckeys.update(converter.build(user, line, pos, funckey))
        return funckeys


class LineDeviceUpdater(object):

    def __init__(self, line_dao, extension_dao, line_extension_dao, device_dao):
        self.line_dao = line_dao
        self.extension_dao = extension_dao
        self.line_extension_dao = line_extension_dao
        self.device_dao = device_dao

    def update(self, device):
        converters = self.get_converters(device)
        self.device_dao.update_lines(device, converters)
        if not converters:
            self.device_dao.reset_autoprov(device)

    def get_converters(self, device):
        converters = []
        lines = self.line_dao.find_all_by(device=device.id)
        for line in lines:
            converter = self.build_line_converter(line)
            if converter:
                converters.append(converter)
        return converters

    def build_line_converter(self, line):
        registrar = self.device_dao.get_registrar(line.configregistrar)
        if line.protocol == 'sip':
            return self.build_sip_converter(line, registrar)
        elif line.protocol == 'sccp':
            return self.build_sccp_converter(registrar)
        return None

    def build_sip_converter(self, line, registrar):
        extension = self.find_extension_for_line(line)
        if extension:
            return LineSIPConverter(registrar,
                                    line,
                                    extension)
        return None

    def build_sccp_converter(self, registrar):
        return LineSCCPConverter(registrar)

    def find_extension_for_line(self, line):
        line_extension = self.line_extension_dao.find_by_line_id(line.id)
        if line_extension:
            return self.extension_dao.get(line_extension.extension_id)
        return None


class SearchEngine(object):

    PROVD_DEVICE_KEYS = [
        'id',
        'ip',
        'mac',
        'sn',
        'plugin',
        'vendor',
        'model',
        'version',
        'description',
        'options',
    ]

    DEFAULT_ORDER = 'ip'
    DEFAULT_DIRECTION = 'asc'

    def __init__(self, provd_dao):
        self.provd_dao = provd_dao

    def search(self, parameters):
        self.validate_parameters(parameters)
        provd_devices = self.provd_dao.find_all_devices(parameters.get('order', self.DEFAULT_ORDER),
                                                        parameters.get('direction', self.DEFAULT_DIRECTION))

        provd_devices = self.filter_devices(provd_devices,
                                            parameters.get('search'))

        total = len(provd_devices)

        provd_devices = self.paginate_devices(provd_devices,
                                              parameters.get('offset', parameters.get('skip', 0)),
                                              parameters.get('limit'))

        items = [self.provd_dao.build_provd_device(device).extract_model()
                 for device in provd_devices]

        return SearchResult(total=total, items=items)

    def validate_parameters(self, parameters):
        if 'direction' in parameters:
            if parameters['direction'] not in self.provd_dao.DIRECTION:
                raise errors.invalid_direction(parameters['direction'], self.provd_dao.DIRECTION)

        if 'order' in parameters:
            if parameters['order'] not in self.PROVD_DEVICE_KEYS:
                raise errors.invalid_ordering(parameters['order'], self.PROVD_DEVICE_KEYS)

    def filter_devices(self, devices, search=None):
        if search is None:
            return devices

        search = search.lower()

        return [device for device in devices
                if self._matches_search(device, search)]

    def _matches_search(self, device, search_lowered):
        for key in self.PROVD_DEVICE_KEYS:
            if key in device and search_lowered in unicode(device[key]).lower():
                return True
        return False

    def paginate_devices(self, devices, offset=0, limit=None):
        if limit:
            return devices[offset:offset + limit]
        return devices[offset:]