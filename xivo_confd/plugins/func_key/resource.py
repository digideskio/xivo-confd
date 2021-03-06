# -*- coding: UTF-8 -*-

# Copyright (C) 2016 Avencall
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

from flask import url_for, request

from xivo_confd.authentication.confd_auth import required_acl
from xivo_confd.helpers.restful import ItemResource, ListResource, ConfdResource

from xivo_dao.resources.func_key_template.model import FuncKeyTemplate

from xivo_dao.resources.func_key.model import FuncKey
from xivo_dao.resources.func_key.model import (AgentDestination,
                                               BSFilterDestination,
                                               ConferenceDestination,
                                               CustomDestination,
                                               ForwardDestination,
                                               GroupDestination,
                                               OnlineRecordingDestination,
                                               PagingDestination,
                                               ParkPositionDestination,
                                               ParkingDestination,
                                               QueueDestination,
                                               ServiceDestination,
                                               TransferDestination,
                                               UserDestination)
from .schema import (FuncKeyDestinationField,
                     FuncKeySchema,
                     FuncKeyUnifiedTemplateSchema,
                     FuncKeyTemplateSchema,
                     FuncKeyTemplateUserSchema)


models_destination = {'user': UserDestination,
                      'group': GroupDestination,
                      'queue': QueueDestination,
                      'conference': ConferenceDestination,
                      'paging': PagingDestination,
                      'service': ServiceDestination,
                      'custom': CustomDestination,
                      'forward': ForwardDestination,
                      'transfer': TransferDestination,
                      'park_position': ParkPositionDestination,
                      'parking': ParkingDestination,
                      'bsfilter': BSFilterDestination,
                      'agent': AgentDestination,
                      'onlinerec': OnlineRecordingDestination}


def _create_funckey_model(funckey):
    type_ = funckey['destination'].pop('type')
    funckey['destination'] = models_destination[type_](**funckey['destination'])
    return FuncKey(**funckey)


class FuncKeyDestination(ConfdResource):

    @required_acl('confd.funckeys.destinations.read')
    def get(self):
        return [{'type': type_,
                 'parameters': funckey().get_parameters()}
                for type_, funckey in FuncKeyDestinationField.destination_schemas.iteritems()]


class FuncKeyTemplateList(ListResource):

    schema = FuncKeyTemplateSchema(context={'exclude_destination': ['agent', 'bsfilter']})
    model = FuncKeyTemplate

    def build_headers(self, template):
        return {'Location': url_for('func_keys_templates', id=template.id, _external=True)}

    @required_acl('confd.funckeys.templates.read')
    def get(self):
        params = self.search_params()
        result = self.service.search(params)
        return {'total': result.total,
                'items': [self.schema.dump(item).data for item in result.items]}

    @required_acl('confd.funckeys.templates.create')
    def post(self):
        template = self.schema.load(request.get_json()).data
        template_model = self._create_template_model(template)
        model = self.service.create(template_model)
        return self.schema.dump(model).data, 201, self.build_headers(model)

    def _create_template_model(self, template):
        for position, funckey in template.get('keys', {}).iteritems():
            template['keys'][position] = _create_funckey_model(funckey)
        return self.model(**template)


class FuncKeyTemplateItem(ConfdResource):

    schema = FuncKeyTemplateSchema(context={'exclude_destination': ['agent', 'bsfilter']})

    def __init__(self, service):
        super(FuncKeyTemplateItem, self).__init__()
        self.service = service

    @required_acl('confd.funckeys.templates.{id}.read')
    def get(self, id):
        template = self.service.get(id)
        return self.schema.dump(template).data

    @required_acl('confd.funckeys.templates.{id}.delete')
    def delete(self, id):
        template = self.service.get(id)
        self.service.delete(template)
        return '', 204


class FuncKeyTemplateItemPosition(ItemResource):

    schema = FuncKeySchema(context={'exclude_destination': ['agent', 'bsfilter']})

    @required_acl('confd.funckeys.templates.{id}.{position}.read')
    def get(self, id, position):
        funckey = self.service.get(id).get(position)
        return self.schema.dump(funckey).data

    @required_acl('confd.funckeys.templates.{id}.{position}.update')
    def put(self, id, position):
        template = self.service.get(id)
        funckey = self.schema.load(request.get_json()).data
        funckey_model = _create_funckey_model(funckey)
        self.service.edit_funckey(funckey_model, template, position)
        return '', 204

    @required_acl('confd.funckeys.templates.{id}.{position}.delete')
    def delete(self, id, position):
        template = self.service.get(id)
        self.service.delete_funckey(template, position)
        return '', 204


class UserFuncKey(ConfdResource):

    def __init__(self, service, user_dao, template_dao):
        super(UserFuncKey, self).__init__()
        self.service = service
        self.user_dao = user_dao
        self.template_dao = template_dao

    def get_user(self, user_id):
        return self.user_dao.get_by_id_uuid(user_id)


class UserFuncKeyList(UserFuncKey):

    schema = FuncKeyUnifiedTemplateSchema()

    @required_acl('confd.users.{user_id}.funckeys.read')
    def get(self, user_id):
        template = self.service.get_unified_template(user_id)
        return self.schema.dump(template).data


class UserFuncKeyItemPosition(UserFuncKey):

    schema = FuncKeySchema()

    @required_acl('confd.users.{user_id}.funckeys.{position}.update')
    def put(self, user_id, position):
        user = self.user_dao.get_by_id_uuid(user_id)
        template = self.template_dao.get(user.private_template_id)
        funckey = self.schema.load(request.get_json()).data
        funckey_model = _create_funckey_model(funckey)
        self.service.edit_user_funckey(user, funckey_model, template, position)
        return '', 204

    @required_acl('confd.users.{user_id}.funckeys.{position}.delete')
    def delete(self, user_id, position):
        user = self.user_dao.get_by_id_uuid(user_id)
        template = self.template_dao.get(user.private_template_id)
        self.service.delete_funckey(template, position)
        return '', 204

    @required_acl('confd.users.{user_id}.funckeys.{position}.read')
    def get(self, user_id, position):
        template = self.service.get_unified_template(user_id)
        funckey = template.get(position)
        return self.schema.dump(funckey).data


class UserFuncKeyTemplate(ConfdResource):

    def __init__(self, service, user_dao, template_dao):
        super(UserFuncKeyTemplate, self).__init__()
        self.service = service
        self.user_dao = user_dao
        self.template_dao = template_dao

    def get_user(self, user_id):
        return self.user_dao.get_by_id_uuid(user_id)


class UserFuncKeyTemplateAssociation(UserFuncKeyTemplate):

    @required_acl('confd.users.{user_id}.funckeys.templates.{template_id}.update')
    def put(self, user_id, template_id):
        user = self.get_user(user_id)
        template = self.template_dao.get(template_id)
        self.service.associate(user, template)
        return '', 204

    @required_acl('confd.users.{user_id}.funckeys.templates.{template_id}.delete')
    def delete(self, user_id, template_id):
        user = self.get_user(user_id)
        template = self.template_dao.get(template_id)
        self.service.dissociate(user, template)
        return '', 204


class UserFuncKeyTemplateGet(UserFuncKeyTemplate):

    schema = FuncKeyTemplateUserSchema()

    @required_acl('confd.users.{user_id}.funckeys.templates.read')
    def get(self, user_id):
        user = self.get_user(user_id)
        result = self.service.find_all_by_user_id(user.id)
        return {'total': len(result),
                'items': [self.schema.dump(item).data for item in result]}


class FuncKeyTemplateUserGet(UserFuncKeyTemplate):

    schema = FuncKeyTemplateUserSchema()

    @required_acl('confd.funckeys.templates.{template_id}.users.read')
    def get(self, template_id):
        template = self.template_dao.get(template_id)
        result = self.service.find_all_by_template_id(template.id)
        return {'total': len(result),
                'items': [self.schema.dump(item).data for item in result]}
