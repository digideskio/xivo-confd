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

import unittest
from mock import sentinel, Mock
from hamcrest import assert_that, equal_to, is_not, has_key, calling, raises

from xivo_confd.helpers.converter import Converter

from xivo_confd.resources.func_keys.service import TemplateService
from xivo_confd.resources.func_keys.resource import UserFuncKeyResource, TemplateManipulator
from xivo_confd.resources.func_keys.validator import BSFilterValidator
from xivo_confd.resources.devices.service import DeviceUpdater

from xivo_dao.helpers.exception import ResourceError, NotFoundError
from xivo_dao.resources.user.model import User
from xivo_dao.resources.func_key.model import FuncKey
from xivo_dao.resources.func_key_template.model import FuncKeyTemplate


class TestFuncKeyManipulator(unittest.TestCase):

    def setUp(self):
        self.service = Mock(TemplateService)
        self.device_updater = Mock(DeviceUpdater)
        self.user_dao = Mock()
        self.manipulator = TemplateManipulator(self.service, self.device_updater, self.user_dao)

    def test_when_updating_func_key_then_updates_template(self):
        funckey = Mock(FuncKey)
        expected_funckey = Mock(FuncKey)

        template = FuncKeyTemplate(keys={1: funckey})
        self.service.get.return_value = template

        self.manipulator.update_funckey(sentinel.template_id, 1, expected_funckey)

        assert_that(template.keys[1], equal_to(expected_funckey))
        self.service.get.assert_called_once_with(sentinel.template_id)
        self.service.edit.assert_called_once_with(template)

    def test_given_position_does_not_exist_when_updating_then_adds_key(self):
        expected_funckey = Mock(FuncKey)

        template = FuncKeyTemplate(keys={})
        self.service.get.return_value = template

        self.manipulator.update_funckey(sentinel.template_id, 2, expected_funckey)

        assert_that(template.keys[2], equal_to(expected_funckey))

    def test_when_deleting_func_key_then_removes_func_key_from_template(self):
        funckey = Mock(FuncKey)
        template = FuncKeyTemplate(keys={1: funckey})
        self.service.get.return_value = template

        self.manipulator.remove_funckey(sentinel.template_id, 1)

        assert_that(template.keys, is_not(has_key(1)))
        self.service.get.assert_called_once_with(sentinel.template_id)
        self.service.edit.assert_called_once_with(template)

    def test_given_template_is_empty_when_deleting_func_key_then_returns_success(self):
        template = FuncKeyTemplate(keys={})
        self.service.get.return_value = template

        self.manipulator.remove_funckey(sentinel.template_id, 1)

    def test_when_associating_template_then_adds_template_to_user(self):
        self.service.get.return_value = FuncKeyTemplate(id=sentinel.public_template_id)
        self.user_dao.get.return_value = User(id=sentinel.user_id,
                                              private_template_id=sentinel.private_template_id)

        expected_user = User(id=sentinel.user_id,
                             private_template_id=sentinel.private_template_id,
                             func_key_template_id=sentinel.public_template_id)

        self.manipulator.associate_user(sentinel.template_id, sentinel.user_id)

        self.user_dao.edit.assert_called_once_with(expected_user)
        self.device_updater.update_for_user.assert_called_once_with(expected_user)

    def test_when_associating_private_template_then_raises_error(self):
        self.service.get.return_value = FuncKeyTemplate(id=sentinel.private_template_id,
                                                        private=True)
        self.user_dao.get.return_value = User(id=sentinel.user_id)

        assert_that(
            calling(self.manipulator.associate_user).with_args(sentinel.template_id, sentinel.user_id),
            raises(ResourceError))

    def test_when_dissociating_public_template_then_removes_template_from_user(self):
        self.user_dao.get.return_value = User(id=sentinel.user_id,
                                              private_template_id=sentinel.private_template_id,
                                              func_key_template_id=sentinel.public_template_id)

        expected_user = User(id=sentinel.user_id,
                             private_template_id=sentinel.private_template_id,
                             func_key_template_id=None)

        self.manipulator.dissociate_user(sentinel.public_template_id, sentinel.user_id)

        self.user_dao.edit.assert_called_once_with(expected_user)
        self.device_updater.update_for_user.assert_called_once_with(expected_user)

    def test_when_dissociating_unknown_template_then_raises_error(self):
        self.user_dao.get.return_value = User(id=sentinel.user_id,
                                              private_template_id=sentinel.private_template_id,
                                              func_key_template_id=sentinel.other_template_id)

        assert_that(
            calling(self.manipulator.dissociate_user).with_args(sentinel.template_id, sentinel.user_id),
            raises(NotFoundError))

    def test_when_fetching_unified_template_then_merges_funckeys(self):
        self.user_dao.get.return_value = User(id=sentinel.user_id,
                                              private_template_id=sentinel.private_template_id,
                                              func_key_template_id=sentinel.public_template_id)

        public_funckey = Mock(FuncKey)
        private_funckey = Mock(FuncKey)

        public_template = FuncKeyTemplate(keys={1: public_funckey})
        private_template = FuncKeyTemplate(keys={2: private_funckey})

        self.service.get.side_effect = [public_template, private_template]

        expected_template = FuncKeyTemplate(keys={1: public_funckey,
                                                  2: private_funckey})

        result = self.manipulator.get_unified_template(sentinel.user_id)

        assert_that(result, equal_to(expected_template))

    def test_given_no_template_associated_when_fetching_unified_template_then_returns_private_template(self):
        self.user_dao.get.return_value = User(id=sentinel.user_id,
                                              private_template_id=sentinel.private_template_id,
                                              func_key_template_id=None)

        private_funckey = Mock(FuncKey)
        private_template = FuncKeyTemplate(keys={1: private_funckey})
        self.service.get.return_value = private_template

        result = self.manipulator.get_unified_template(sentinel.user_id)

        assert_that(result, equal_to(private_template))


class TestUserFuncKeyResource(unittest.TestCase):

    def setUp(self):
        self.manipulator = Mock(TemplateManipulator)
        self.converter = Mock(Converter)
        self.validator = Mock(BSFilterValidator)

        self.user = User(id=sentinel.user_id,
                         private_template_id=sentinel.private_template_id)
        self.user_dao = Mock()
        self.user_dao.get.return_value = self.user

        self.resource = UserFuncKeyResource(self.manipulator,
                                            self.converter,
                                            self.validator,
                                            self.user_dao)

    def test_when_updating_func_key_then_calls_bsfilter_validator(self):
        funckey = self.converter.decode.return_value = Mock(FuncKey)

        self.resource.update_funckey(sentinel.user_id, 1)

        self.validator.validate.assert_called_once_with(self.user, funckey)