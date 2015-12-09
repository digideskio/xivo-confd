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


from flask_restful import fields, marshal

from xivo_dao.helpers.db_manager import Session

from xivo_confd.helpers.restful import ConfdResource
from xivo_confd.plugins.user_import import csvparse
from xivo_confd import sysconfd, bus

entry_fields = {
    'row_number': fields.Integer(default=None),
    'user_id': fields.Integer(default=None),
    'voicemail_id': fields.Integer(default=None),
    'line_id': fields.Integer(default=None),
    'sip_id': fields.Integer(default=None),
    'sccp_id': fields.Integer(default=None),
    'extension_id': fields.Integer(default=None),
    'incall_extension_id': fields.Integer(default=None),
    'cti_profile_id': fields.Integer(default=None),
}


class UserImportResource(ConfdResource):

    def __init__(self, service):
        self.service = service

    def post(self):
        parser = csvparse.parse()
        entries, errors = self.service.import_rows(parser)

        if errors:
            status_code = 400
            response = {'errors': errors}
            self.rollback()
        else:
            status_code = 201
            response = {'created': [marshal(entry, entry_fields) for entry in entries]}

        return response, status_code

    def rollback(self):
        Session.rollback()
        sysconfd.rollback()
        bus.rollback()