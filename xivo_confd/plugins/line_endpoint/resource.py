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


from flask_restful import marshal

from flask_restful import fields
from xivo_confd.authentication.confd_auth import required_acl
from xivo_confd.helpers.restful import ConfdResource
from xivo_confd.helpers.restful import Link, FieldList


sccp_fields = {
    'line_id': fields.Integer,
    'endpoint_id': fields.Integer,
    'endpoint': fields.String,
    'links': FieldList(Link('lines',
                            field='line_id',
                            target='id'),
                       Link('endpoint_sccp',
                            field='endpoint_id',
                            target='id'))
}


sip_fields = {
    'line_id': fields.Integer,
    'endpoint_id': fields.Integer,
    'endpoint': fields.String,
    'links': FieldList(Link('lines',
                            field='line_id',
                            target='id'),
                       Link('endpoint_sip',
                            field='endpoint_id',
                            target='id'))
}

custom_fields = {
    'line_id': fields.Integer,
    'endpoint_id': fields.Integer,
    'endpoint': fields.String,
    'links': FieldList(Link('lines',
                            field='line_id',
                            target='id'),
                       Link('endpoint_custom',
                            field='endpoint_id',
                            target='id'))
}


class LineEndpoint(ConfdResource):

    def __init__(self, service):
        super(LineEndpoint, self).__init__()
        self.service = service


class LineEndpointAssociation(LineEndpoint):

    def put(self, line_id, endpoint_id):
        line = self.service.get_line(line_id)
        endpoint = self.service.get_endpoint(endpoint_id)
        self.service.associate(line, endpoint)
        return '', 204

    def delete(self, line_id, endpoint_id):
        line = self.service.get_line(line_id)
        endpoint = self.service.get_endpoint(endpoint_id)
        self.service.dissociate(line, endpoint)
        return '', 204


class LineEndpointGet(LineEndpoint):

    def get(self, line_id):
        line_endpoint = self.service.get_association_from_line(line_id)
        return marshal(line_endpoint, self.fields)


class EndpointLineGet(LineEndpoint):

    def get(self, endpoint_id):
        line_endpoint = self.service.get_association_from_endpoint(endpoint_id)
        return marshal(line_endpoint, self.fields)


class LineEndpointAssociationSip(LineEndpointAssociation):

    @required_acl('confd.lines.{line_id}.endpoints.sip.{endpoint_id}.update')
    def put(self, line_id, endpoint_id):
        return super(LineEndpointAssociationSip, self).put(line_id, endpoint_id)

    @required_acl('confd.lines.{line_id}.endpoints.sip.{endpoint_id}.delete')
    def delete(self, line_id, endpoint_id):
        return super(LineEndpointAssociationSip, self).delete(line_id, endpoint_id)


class LineEndpointGetSip(LineEndpointGet):
    fields = sip_fields

    @required_acl('confd.lines.{line_id}.endpoints.sip.read')
    def get(self, line_id):
        return super(LineEndpointGetSip, self).get(line_id)


class EndpointLineGetSip(EndpointLineGet):
    fields = sip_fields

    @required_acl('confd.endpoints.sip.{endpoint_id}.lines.read')
    def get(self, endpoint_id):
        return super(EndpointLineGetSip, self).get(endpoint_id)


class LineEndpointAssociationSccp(LineEndpointAssociation):

    @required_acl('confd.lines.{line_id}.endpoints.sccp.{endpoint_id}.update')
    def put(self, line_id, endpoint_id):
        return super(LineEndpointAssociationSccp, self).put(line_id, endpoint_id)

    @required_acl('confd.lines.{line_id}.endpoints.sccp.{endpoint_id}.delete')
    def delete(self, line_id, endpoint_id):
        return super(LineEndpointAssociationSccp, self).delete(line_id, endpoint_id)


class LineEndpointGetSccp(LineEndpointGet):
    fields = sccp_fields

    @required_acl('confd.lines.{line_id}.endpoints.sccp.read')
    def get(self, line_id):
        return super(LineEndpointGetSccp, self).get(line_id)


class EndpointLineGetSccp(EndpointLineGet):
    fields = sccp_fields

    @required_acl('confd.endpoints.sccp.{endpoint_id}.lines.read')
    def get(self, endpoint_id):
        return super(EndpointLineGetSccp, self).get(endpoint_id)


class LineEndpointAssociationCustom(LineEndpointAssociation):

    @required_acl('confd.lines.{line_id}.endpoints.custom.{endpoint_id}.update')
    def put(self, line_id, endpoint_id):
        return super(LineEndpointAssociationCustom, self).put(line_id, endpoint_id)

    @required_acl('confd.lines.{line_id}.endpoints.custom.{endpoint_id}.delete')
    def delete(self, line_id, endpoint_id):
        return super(LineEndpointAssociationCustom, self).delete(line_id, endpoint_id)


class LineEndpointGetCustom(LineEndpointGet):
    fields = custom_fields

    @required_acl('confd.lines.{line_id}.endpoints.custom.read')
    def get(self, line_id):
        return super(LineEndpointGetCustom, self).get(line_id)


class EndpointLineGetCustom(EndpointLineGet):
    fields = custom_fields

    @required_acl('confd.endpoints.custom.{endpoint_id}.lines.read')
    def get(self, endpoint_id):
        return super(EndpointLineGetCustom, self).get(endpoint_id)
