# -*- coding: UTF-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import re
import string

from xivo_confd.helpers.validator import ValidationGroup, RequiredFields, Optional, UniqueField, RegexField
from xivo_dao.resources.endpoint_sip import dao

NAME_REGEX = r"^[a-zA-Z0-9_-]{1,40}$"
SECRET_REGEX = r"^[{}]{{1,80}}$".format(re.escape(string.printable))


class UsernameChanged(UniqueField):

    def __init__(self, field, dao_find, dao_get):
        super(UsernameChanged, self).__init__(field, dao_find, 'SIPEndpoint')
        self.dao_get = dao_get

    def validate(self, model):
        existing = self.dao_get(model.id)
        existing_value = getattr(existing, self.field)
        new_value = getattr(model, self.field)
        if existing_value != new_value:
            super(UsernameChanged, self).validate(model)


def build_validator():
    return ValidationGroup(
        common=[
            Optional('name',
                     RegexField.compile('name', NAME_REGEX, "username must only use alphanumeric characters")),
            Optional('secret',
                     RegexField.compile('secret', SECRET_REGEX))
        ],
        create=[
            Optional('name',
                     UniqueField('name',
                                 lambda v: dao.find_by(name=v),
                                 'SIPEndpoint'),
                     RegexField.compile('name', NAME_REGEX)
                     ),
            Optional('secret',
                     RegexField.compile('secret', SECRET_REGEX)
                     ),
        ],
        edit=[
            RequiredFields('name', 'secret', 'type', 'host'),
            UsernameChanged('name',
                            lambda v: dao.find_by(name=v),
                            dao.get),
        ])
