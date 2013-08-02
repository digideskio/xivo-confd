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

import subprocess
import os
import logging

from xivo_dao import agent_dao, recordings_dao
from xivo_restapi import config
from xivo_restapi.v1_0.restapi_config import RestAPIConfig
from xivo_restapi.v1_0.services.utils.exceptions import InvalidInputException

logger = logging.getLogger(__name__)
data_access_logger = logging.getLogger(config.DATA_ACCESS_LOGGERNAME)


class RecordingManagement(object):

    def __init__(self):
        pass

    def add_recording(self, campaign_id, recording):
        data_access_logger.info("Adding a recording to the campaign %d with data %s."
                                % (campaign_id, recording.todict()))
        if 'agent_no' in vars(recording):
            try:
                recording.agent_id = agent_dao.agent_id(recording.agent_no)
            except LookupError:
                raise InvalidInputException('Could not add the recording', ['No such agent'])
        recording.campaign_id = campaign_id
        result = recordings_dao.add_recording(recording)
        return result

    def get_recordings(self, campaign_id, search=None, paginator=None):
        search_pattern = {}
        if search is not None:
            for item in search:
                if (item == 'agent_no'):
                    search_pattern["agent_id"] = agent_dao.agent_id(search['agent_no'])
                else:
                    search_pattern[item] = search[item]
        (total, items) = recordings_dao.get_recordings(campaign_id,
                                                       search_pattern,
                                                       paginator)
        self._insert_agent_no(items)
        return (total, items)

    def search_recordings(self, campaign_id, search, paginator=None):
        if search is None or search == {} or 'key' not in search:
            return self.get_recordings(campaign_id, {}, paginator)
        else:
            (total, items) = recordings_dao.search_recordings(campaign_id,
                                                              search['key'],
                                                              paginator)
            self._insert_agent_no(items)
            return (total, items)

    def _insert_agent_no(self, items):
        for recording in items:
            recording.agent_no = agent_dao.agent_number(recording.agent_id)
        return items

    def delete(self, campaign_id, recording_id):
        data_access_logger.info("Deleting recording of id %s in campaign %d."
                                % (recording_id, campaign_id))
        filename = recordings_dao.delete(campaign_id, recording_id)
        if filename is None:
            logger.error("Recording file remove error - no filename!")
            return False
        else:
            filepath = os.path.join(RestAPIConfig.RECORDING_FILE_ROOT_PATH, filename)
            logger.debug("Deleting file: %s", filepath)

            logphrase = "File %s is being deleted." % filename
            cmd = ['logger', '-t', 'xivo-recording', '"%s"' % logphrase]
            subprocess.check_call(cmd)
            os.remove(filepath)
            return True