# -*- coding: utf-8 -*-
from xivo_dao import voicemail_dao
from xivo_restapi.services.utils.exceptions import NoSuchElementException
import logging
from xivo_restapi.restapi_config import RestAPIConfig

# Copyright (C) 2013 Avencall
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

data_access_logger = logging.getLogger(RestAPIConfig.DATA_ACCESS_LOGGERNAME)


class VoicemailManagement(object):

    def __init__(self):
        pass

    def get_all_voicemails(self):
        return voicemail_dao.all()

    def edit_voicemail(self, voicemailid, data):
        data_access_logger.info("Editing the voicemail of id %d with data %s."
                                % (voicemailid, data))
        if(voicemail_dao.get(voicemailid) is None):
            raise NoSuchElementException("No such voicemail: " + str(voicemailid))
        voicemail_dao.update(voicemailid, data)
