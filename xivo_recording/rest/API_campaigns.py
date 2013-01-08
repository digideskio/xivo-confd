# -*- coding: UTF-8 -*-

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

from flask import request
from flask.helpers import make_response
from sqlalchemy.exc import IntegrityError
from xivo_recording.dao.exceptions import NoSuchElementException, \
    InvalidInputException
from xivo_recording.services.campagne_management import CampagneManagement
import logging
import rest_encoder


logger = logging.getLogger(__name__)


class APICampaigns(object):

    def __init__(self):
        self._campagne_manager = CampagneManagement()

    def add_campaign(self):
        try:
            body = rest_encoder.decode(request.data)
            logger.debug(str(body))
        except ValueError:
            body = "No parsable data in the request, data: " + request.data
            return make_response(body, 400)
        body = self._campagne_manager.supplement_add_input(body)
        try:
            result = self._campagne_manager.create_campaign(body)
        except IntegrityError:
            liste = ["duplicated_name"]
            return make_response(rest_encoder.encode(liste), 400)
        except InvalidInputException as e:
            liste = e.errors_list
            return make_response(rest_encoder.encode(liste), 400)
        if (type(result) == int and result > 0):
            return make_response(str(result), 201)
        else:
            return make_response(str(result), 500)

    def get(self, campaign_id=None):
        try:
            logger.debug("Get args:" + str(campaign_id))
            checkCurrentlyRunning = False
            params = {}
            if campaign_id != None:
                params['id'] = campaign_id
            for item in request.args:
                if item == 'running':
                    checkCurrentlyRunning = (request.args[item] == 'true')
                else:
                    params[item] = request.args[item]
            result = self._campagne_manager.get_campaigns_as_dict(params, checkCurrentlyRunning)
            logger.debug("got result")
            body = rest_encoder.encode(result)
            logger.debug("result encoded")
            return make_response(body, 200)
        except Exception as e:
            logger.debug("got exception:" + str(e.args))
            return make_response(str(e.args), 500)

    def delete(self, resource_id):
        try:
            body = rest_encoder.decode(request.data)
        except ValueError:
            body = "No parsable data in the request"
        return make_response(("Work in progress, root delete, resource_id: " +
                              str(resource_id) +
                              " body: " + str(body) +
                              " args: " + str(request.args)),
                             501)

    def update(self, campaign_id):
        try:
            body = rest_encoder.decode(request.data)
            logger.debug(str(body))
        except ValueError:
            body = "No parsable data in the request, data: " + request.data
            return make_response(body, 400)
        try:
            body = self._campagne_manager.supplement_edit_input(body)
            result = self._campagne_manager.update_campaign(campaign_id, body)
        except NoSuchElementException:
            liste = ["campaign_not_found"]
            return make_response(rest_encoder.encode(liste), 404)
        except IntegrityError:
            liste = ["duplicated_name"]
            return make_response(rest_encoder.encode(liste), 400)
        except InvalidInputException as e:
            liste = e.errors_list
            return make_response(rest_encoder.encode(liste), 400)
        if (result):
            return make_response(("Updated: " + str(result)), 200)
        else:
            return make_response(str(result), 500)