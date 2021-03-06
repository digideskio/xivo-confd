# -*- coding: utf-8 -*-

# Copyright (C) 2013-2016 Avencall
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

from xivo_confd.plugins.user.validator import build_validator, build_validator_forward
from xivo_confd.plugins.user.notifier import build_notifier, build_notifier_service, build_notifier_forward
from xivo_confd.plugins.device.builder import build_device_updater

from xivo_confd.helpers.resource import CRUDService
from xivo_confd.helpers.validator import ValidationGroup

from xivo_dao.helpers.db_manager import Session
from xivo_dao.resources.user import dao as user_dao


class UserBaseService(CRUDService):

    def get(self, user_id):
        return self.dao.get_by_id_uuid(user_id)


class UserService(UserBaseService):

    def __init__(self, dao, validator, notifier, device_updater):
        super(UserService, self).__init__(dao, validator, notifier)
        self.device_updater = device_updater

    def edit(self, user):
        with Session.no_autoflush:
            self.validator.validate_edit(user)
        self.dao.edit(user)
        self.notifier.edited(user)
        self.device_updater.update_for_user(user)

    def legacy_search(self, term):
        return self.dao.legacy_search(term)


def build_service(provd_client):
    updater = build_device_updater(provd_client)
    return UserService(user_dao,
                       build_validator(),
                       build_notifier(),
                       updater)


class UserCallServiceService(UserBaseService):

    def edit(self, user, schema):
        self.validator.validate_edit(user)
        self.dao.edit(user)
        self.notifier.edited(user, schema)


def build_service_callservice():
    return UserCallServiceService(user_dao,
                                  ValidationGroup(),
                                  build_notifier_service())


class UserForwardService(UserBaseService):

    def edit(self, user, schema):
        self.validator.validate_edit(user)
        self.dao.edit(user)
        self.notifier.edited(user, schema)


def build_service_forward():
    return UserForwardService(user_dao,
                              build_validator_forward(),
                              build_notifier_forward())
