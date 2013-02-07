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
from xivo_dao import queue_dao, record_campaigns_dao
from xivo_restapi.dao.exceptions import DataRetrieveError, \
    NoSuchElementException
import logging

logger = logging.getLogger(__name__)


class CampagneManagement:

    def __init__(self):
        pass

    def create_campaign(self, params):
        result = record_campaigns_dao.add(params)
        return result

    def get_campaigns_as_dict(self, search = {}, checkCurrentlyRunning = False, technical_params = None):
        """
        Calls the DAO and converts data to the final format
        """
        search_pattern = {}
        for item in search:
            if (item == 'queue_name'):
                search_pattern["queue_id"] = queue_dao.id_from_name(search["queue_name"])
            else:
                search_pattern[item] = search[item]
        result = None
        if(technical_params != None and '_page' in technical_params and '_pagesize' in technical_params):
            paginator = (int(technical_params['_page']), int(technical_params['_pagesize']))
            result = record_campaigns_dao.get_records(search, checkCurrentlyRunning, paginator)
        else:
            result = record_campaigns_dao.get_records(search, checkCurrentlyRunning)

        try:
            for item in result['data']:
                if(item['queue_id'] != ''):
                    item["queue_name"] = queue_dao. \
                                            queue_name(item["queue_id"])
                    item["queue_display_name"], item["queue_number"] = queue_dao.\
                                                                        get_display_name_number(item["queue_id"])
        except Exception as e:
            logger.critical("DAO failure(" + str(e) + ")!")
            raise DataRetrieveError("DAO failure(" + str(e) + ")!")

        return result

    def update_campaign(self, campaign_id, params):
        logger.debug('going to update')
        result = record_campaigns_dao.update(campaign_id, params)
        return result

    def supplement_add_input(self, data):
        '''Returns the supplemented input for add'''
        logger.debug("Supplementing input for 'add'")
        for key in data:
            if(data[key] == ''):
                data[key] = None
        if(("start_date" not in data) or data["start_date"] == None):
            data["start_date"] = datetime.now().strftime("%Y-%m-%d")
        if(("end_date" not in data) or data["end_date"] == None):
            data["end_date"] = datetime.now().strftime("%Y-%m-%d")
        return data

    def supplement_edit_input(self, data):
        '''Returns the supplemented input for edit'''
        for key in data:
            if(data[key] == ''):
                data[key] = None
        return data

    def delete(self, campaign_id):
        campaign = record_campaigns_dao.get(int(campaign_id))
        if(campaign == None):
            raise NoSuchElementException("No such campaign")
        else:
            record_campaigns_dao.delete(campaign)
