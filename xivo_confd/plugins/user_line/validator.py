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


from xivo_confd.database import user_line as user_line_db

from xivo_confd.helpers.validator import Validator, AssociationValidator

from xivo_dao.helpers import errors


from xivo_confd.plugins.line_device.validator import ValidateLineHasNoDevice


class UserLineAssociationValidator(Validator):

    def validate(self, user, line):
        self.validate_line_has_endpoint(line)
        self.validate_user_not_already_associated(user)

    def validate_line_has_endpoint(self, line):
        if not line.is_associated():
            raise errors.missing_association('Line', 'Endpoint',
                                             line_id=line.id)

    def validate_user_not_already_associated(self, user):
        line_id = user_line_db.find_line_id_for_user(user.id)
        if line_id:
            raise errors.resource_associated('User', 'Line',
                                             user_id=user.id,
                                             line_id=line_id)


class UserLineDissociationValidator(Validator):

    def validate(self, user, line):
        self.validate_no_secondary_users(user, line)
        ValidateLineHasNoDevice().validate(line)

    def validate_no_secondary_users(self, user, line):
        exists = user_line_db.has_secondary_users(user.id, line.id)
        if exists:
            raise errors.secondary_users(line_id=line.id)


def build_validator():
    return AssociationValidator(
        association=[
            UserLineAssociationValidator()
        ],
        dissociation=[
            UserLineDissociationValidator()
        ]
    )
