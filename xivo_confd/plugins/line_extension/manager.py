# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Avencall
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

import abc

from sqlalchemy import Integer
from sqlalchemy.sql import and_, cast

from xivo_dao.helpers.db_manager import Session
from xivo_dao.helpers import errors

from xivo_dao.alchemy.context import Context
from xivo_dao.alchemy.user_line import UserLine
from xivo_dao.alchemy.extension import Extension
from xivo_dao.alchemy.incall import Incall
from xivo_dao.alchemy.dialaction import Dialaction

from xivo_dao.resources.incall.model import Incall as IncallModel

from xivo_dao.resources.extension import dao as extension_dao
from xivo_dao.resources.incall import dao as incall_dao
from xivo_dao.resources.user_line import dao as user_line_dao
from xivo_dao.resources.line_extension import dao as line_extension_dao

from xivo_confd.plugins.line_extension import validator


class LineExtension(object):

    @classmethod
    def from_models(cls, line, extension):
        return cls(line.id, extension.id)

    def __init__(self, line_id, extension_id):
        self.line_id = line_id
        self.extension_id = extension_id


def build_manager():
    incall = IncallAssociator(validator.build_incall_validator(),
                              user_line_dao,
                              incall_dao,
                              extension_dao)

    internal = InternalAssociator(validator.build_internal_validator(),
                                  line_extension_dao)

    associators = {'incall': incall, 'internal': internal}
    return AssociationManager(associators)


class AssociationManager(object):

    def __init__(self, associators):
        self.associators = associators

    def list(self, line_id):
        user_line_query = (Session.query(UserLine.line_id,
                                         UserLine.extension_id)
                           .filter(UserLine.line_id == line_id)
                           .filter(UserLine.extension_id != None)  # noqa
                           .distinct())

        incall_query = (Session.query(UserLine.line_id,
                                      Extension.id.label('extension_id'))
                        .join(Dialaction,
                              and_(Dialaction.action == 'user',
                                   cast(Dialaction.actionarg1, Integer) == UserLine.user_id,
                                   UserLine.main_line == True))  # noqa
                        .join(Incall,
                              and_(Dialaction.category == 'incall',
                                   cast(Dialaction.categoryval, Integer) == Incall.id))
                        .join(Extension,
                              and_(Incall.exten == Extension.exten,
                                   Incall.context == Extension.context))
                        .filter(UserLine.line_id == line_id))

        return [LineExtension(row.line_id, row.extension_id)
                for row in user_line_query.union(incall_query)]

    def associate(self, line, extension):
        associator = self._get_associator(extension)
        return associator.associate(line, extension)

    def _get_associator(self, extension):
        context_type = (Session.query(Context.contexttype)
                        .filter(Context.name == extension.context)
                        .scalar())

        if context_type not in self.associators:
            raise NotImplementedError("Cannot associate extension with context type '{}'".format(context_type))

        return self.associators[context_type]

    def dissociate(self, line, extension):
        associator = self._get_associator(extension)
        return associator.dissociate(line, extension)

    def get_association(self, line, extension):
        associator = self._get_associator(extension)
        return associator.get_association(line, extension)


class AssociationService(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def associate(self, line, extension):
        return

    @abc.abstractmethod
    def dissociate(self, line, extension):
        return

    @abc.abstractmethod
    def get_association(self, line, extension):
        return


class InternalAssociator(object):

    def __init__(self, validator, dao):
        self.validator = validator
        self.dao = dao

    def associate(self, line, extension):
        self.validator.validate_association(line, extension)
        self.dao.associate(line, extension)
        return LineExtension.from_models(line, extension)

    def dissociate(self, line, extension):
        self.validator.validate_dissociation(line, extension)
        self.dao.dissociate(line, extension)

    def get_association(self, line, extension):
        self.dao.get_by(line_id=line.id, extension_id=extension.id)
        return LineExtension.from_models(line, extension)


class IncallAssociator(object):

    def __init__(self, validator, user_line_dao, incall_dao, extension_dao):
        self.validator = validator
        self.user_line_dao = user_line_dao
        self.incall_dao = incall_dao
        self.extension_dao = extension_dao

    def associate(self, line, extension):
        self.validator.validate_association(line, extension)
        self._create_incall(line, extension)
        return LineExtension.from_models(line, extension)

    def _create_incall(self, line, extension):
        main_user_line = self.user_line_dao.get_by(main_user=True, line_id=line.id)
        incall = IncallModel.user_destination(main_user_line.user_id,
                                              extension.id)
        self.incall_dao.create(incall)

    def dissociate(self, line, extension):
        self.validator.validate_dissociation(line, extension)
        incall = self.incall_dao.find_by_extension_id(extension.id)
        self.incall_dao.delete(incall)

    def get_association(self, line, extension):
        association = self.incall_dao.find_line_extension_by_extension_id(extension.id)
        if not association:
            raise errors.not_found('LineExtension', line_id=line.id, extension_id=extension.id)
        if association.line_id != line.id:
            raise errors.not_found('LineExtension', line_id=line.id, extension_id=extension.id)
        return LineExtension(association.line_id, association.extension_id)
