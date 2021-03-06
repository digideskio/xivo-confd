# -*- coding: utf-8 -*-

# Copyright (C) 2013-2015 Avencall
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

import unittest
from mock import Mock
from hamcrest import assert_that, equal_to
from xivo_confd.resources.configuration.actions import LiveReloadService


class TestLiveReloadService(unittest.TestCase):

    def setUp(self):
        self.dao = Mock()
        self.validator = Mock()
        self.notifier = Mock()
        self.service = LiveReloadService(self.dao, self.validator, self.notifier)

    def test_when_get_called_then_returns_a_model_with_live_reload_enabled(self):
        self.dao.is_live_reload_enabled.return_value = True

        result = self.service.get()
        assert_that(result.enabled, equal_to(True))

    def test_when_edit_called_then_sets_live_reload_status(self):
        live_reload = Mock()
        expected_data = live_reload.dao_dict.return_value = {'enabled': True}

        self.service.edit(live_reload)

        self.validator.validate_live_reload_data.assert_called_once_with(expected_data)
        self.dao.set_live_reload_status.assert_called_once_with(expected_data)
        self.notifier.live_reload_status_changed.assert_called_once_with(expected_data)
