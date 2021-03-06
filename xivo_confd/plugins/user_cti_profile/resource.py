# -*- coding: UTF-8 -*-

# Copyright (C) 2015-2016 Avencall
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


from flask_restful import reqparse, fields, marshal

from xivo_confd.authentication.confd_auth import required_acl
from xivo_confd.helpers.restful import FieldList, Link, ConfdResource


fields = {
    'user_id': fields.Integer,
    'enabled': fields.Boolean,
    'cti_profile_id': fields.Integer(default=None),
    'links': FieldList(Link('cti_profiles',
                            route='cti_profiles.get',
                            field='cti_profile_id',
                            target='resource_id'),
                       Link('users',
                            field='user_id',
                            target='id'))
}

parser = reqparse.RequestParser()
parser.add_argument('cti_profile_id', type=int, store_missing=False)
parser.add_argument('enabled', type=bool, store_missing=False)


class UserCtiProfileRoot(ConfdResource):

    def __init__(self, service, user_dao, cti_profile_dao):
        super(ConfdResource, self).__init__()
        self.service = service
        self.user_dao = user_dao
        self.cti_profile_dao = cti_profile_dao

    @required_acl('confd.users.{user_id}.cti.read')
    def get(self, user_id):
        user = self.user_dao.get_by_id_uuid(user_id)
        association = self.service.get(user.id)
        return marshal(association, fields)

    @required_acl('confd.users.{user_id}.cti.update')
    def put(self, user_id):
        form = parser.parse_args()
        user = self.user_dao.get_by_id_uuid(user_id)
        association = self.service.get(user.id)
        self.update_model(association, form)
        self.service.edit(association)
        return '', 204

    def update_model(self, association, form):
        for key, value in form.iteritems():
            setattr(association, key, value)
