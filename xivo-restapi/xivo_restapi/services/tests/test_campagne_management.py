# -*- coding: UTF-8 -*-
#
# Copyright (C) 2012  Avencall
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

from datetime import datetime
from mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from xivo_dao import queue_dao, record_campaigns_dao
from xivo_dao.alchemy.record_campaigns import RecordCampaigns
from xivo_restapi.dao.exceptions import NoSuchElementException
import copy
import random
import unittest


class FakeDate(datetime):
        "A manipulable date replacement"
        def __init__(self):
            pass

        @classmethod
        def now(cls):
            return datetime(year=2012, month=1, day=1)


class TestCampagneManagement(unittest.TestCase):

    def setUp(self):
        self.queue_name = 'queuename'
        self.queue_display_name = "queuedisplayname"
        self.queue_number = '1000'

        self.patcher_datetime = patch("datetime.datetime", FakeDate)
        mock_patch_datetime = self.patcher_datetime.start()
        self.instance_datetime = FakeDate
        mock_patch_datetime.return_value = self.instance_datetime

        from xivo_restapi.services.campagne_management import CampagneManagement
        self._campagneManager = CampagneManagement()
        queue_dao.id_from_name = Mock(return_value='1')
        queue_dao.queue_name = Mock(return_value=self.queue_name)
        queue_dao.get_display_name_number = Mock(
                                  return_value=(self.queue_display_name,
                                                self.queue_number))
        self._campaignName = "test-campagne" + str(random.randint(10, 99))

    def test_create_campaign(self):
        campagne_name = "campagne"
        queue_id = "1"
        base_filename = campagne_name + "-"

        data = {
            "campagne_name": campagne_name,
            "activated": False,
            "base_filename": base_filename,
            "queue_id": queue_id
        }
        record_campaigns_dao.add = Mock()
        record_campaigns_dao.add.return_value = 1

        result = self._campagneManager.create_campaign(data)
        self.assertTrue(result == 1)

        record_campaigns_dao.add.assert_called_with(data)

    def test_get_campaigns_as_dict(self):
        campagne_name = "campagne"
        queue_id = "1"
        base_filename = campagne_name + "-"

        data = {'total': 1,
                'data': [{"campagne_name": campagne_name,
                        "activated": False,
                        "base_filename": base_filename,
                        "queue_id": queue_id
                        }]
                }
        #on recopie data dans old_data, car data sera modifié par effet de bord
        old_data = copy.deepcopy(data)
        old_data['data'][0]['queue_name'] = self.queue_name
        old_data['data'][0]['queue_display_name'] = self.queue_display_name
        old_data['data'][0]['queue_number'] = self.queue_number

        record_campaigns_dao.get_records = Mock()
        record_campaigns_dao.get_records.return_value = data
        self.assertEqual(self._campagneManager.get_campaigns_as_dict(),
                         old_data)
        record_campaigns_dao.get_records.assert_called_with({},
                                                                       False)

    def test_update_campaign(self):
        campaign_id = 1
        campagne_name = "campagne"
        queue_id = "1"
        base_filename = campagne_name + "-"

        data = {"campagne_name": campagne_name,
                "activated": False,
                "base_filename": base_filename,
                "queue_id": queue_id
                }
        record_campaigns_dao.update = Mock()
        record_campaigns_dao.update.return_value = True
        self.assertTrue(self._campagneManager.update_campaign(campaign_id,
                                                              data))
        record_campaigns_dao.update.assert_called_with(campaign_id,
                                                                  data)

    def test_supplement_add_input(self):
        data = {"champ1": "valeur1",
                "champ2": "valeur2",
                "champ3": ""}
        old_data = copy.deepcopy(data)
        result = self._campagneManager.supplement_add_input(data)
        old_data["champ3"] = None
        old_data["end_date"] = FakeDate.now().strftime("%Y-%m-%d")
        old_data["start_date"] = FakeDate.now().strftime("%Y-%m-%d")
        self.assertTrue(old_data == result)

    def test_supplement_edit_input(self):
        data = {"champ1": "valeur1",
                "champ2": "valeur2",
                "champ3": ""}
        old_data = copy.deepcopy(data)
        result = self._campagneManager.supplement_edit_input(data)
        old_data["champ3"] = None
        self.assertTrue(old_data == result)

    def test_delete_no_such_element(self):
        record_campaigns_dao.get = Mock()
        record_campaigns_dao.get.return_value = None
        self.assertRaises(NoSuchElementException, self._campagneManager.delete, '1')

    def test_delete_integrity_error(self):
        def mock_delete(campaign):
            raise IntegrityError(None, None, None)
        record_campaigns_dao.delete = Mock()
        record_campaigns_dao.delete.side_effect = mock_delete
        record_campaigns_dao.get = Mock()
        record_campaigns_dao.get.return_value = RecordCampaigns()
        self.assertRaises(IntegrityError, self._campagneManager.delete, '1')

    def test_delete_success(self):
        obj = RecordCampaigns()
        record_campaigns_dao.get = Mock()
        record_campaigns_dao.get.return_value = obj
        record_campaigns_dao.delete = Mock()
        record_campaigns_dao.delete.return_value = None
        self._campagneManager.delete('1')
        record_campaigns_dao.delete.assert_called_with(obj)
