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

from flask import Flask
from hamcrest import assert_that, equal_to
from werkzeug.exceptions import HTTPException, BadRequest

from xivo_confd.helpers import serializer
from xivo_confd.helpers.common import extract_search_parameters, handle_error
from xivo_confd.helpers.mooltiparse.errors import ContentTypeError
from xivo_confd.helpers.mooltiparse.errors import ValidationError
from xivo_dao.helpers.exception import InputError
from xivo_dao.helpers.exception import NotFoundError
from xivo_dao.helpers.exception import ServiceError


class TestCommon(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app = Flask('test')
        app.testing = True
        app.test_request_context('').push()

    def assertResponse(self, response, expected_code, result):
        data, status_code, headers = response
        decoded_response = serializer.decode(data)

        self.assertEquals(status_code, expected_code)
        self.assertEquals(decoded_response, result)


class TestHandleError(TestCommon):

    def test_when_not_found_error_is_raised(self):
        expected_status_code = 404
        expected_message = ["not found error"]
        exception = NotFoundError("not found error")

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_service_error_is_raised(self):
        expected_status_code = 400
        expected_message = ["service error"]
        exception = ServiceError("service error")

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_validation_error_is_raised(self):
        expected_status_code = 400
        expected_message = ["validation error"]
        exception = ValidationError("validation error")

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_content_type_error_is_raised(self):
        expected_status_code = 400
        expected_message = ["content type error"]
        exception = ContentTypeError("content type error")

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_bad_request_is_raised(self):
        expected_status_code = 400
        expected_message = ["bad request"]
        exception = BadRequest("bad request")

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_flask_restful_error_is_raised(self):
        expected_status_code = 400
        expected_message = ["Input Error - field: missing"]

        exception = HTTPException()
        exception.data = {'message': {'field': 'missing'}}
        exception.code = 400

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_generic_http_error_is_raised(self):
        expected_status_code = 400
        expected_message = ["generic http error"]

        exception = HTTPException("generic http error")
        exception.code = 400

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)

    def test_when_generic_exception_is_raised(self):
        expected_status_code = 500
        expected_message = ["Unexpected error: error message"]
        exception = Exception("error message")

        response = handle_error(exception)

        self.assertResponse(response, expected_status_code, expected_message)


class TestExtractSearchParameters(unittest.TestCase):

    def test_given_invalid_skip_then_raises_error(self):
        args = {'skip': 'toto'}
        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_negative_skip_then_raises_error(self):
        args = {'skip': '-1'}
        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_skip_parameter_then_extracts_skip(self):
        expected_result = {'skip': 532}
        args = {'skip': '532'}

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))

    def test_given_invalid_offset_then_raises_error(self):
        args = {'offset': 'toto'}
        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_negative_offset_then_raises_error(self):
        args = {'offset': '-1'}
        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_offset_parameter_then_extracts_offset(self):
        expected_result = {'offset': 532}
        args = {'offset': '532'}

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))

    def test_given_invalid_limit_then_raises_error(self):
        args = {'limit': 'toto'}
        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_negative_limit_then_raises_error(self):
        args = {'limit': '-1'}
        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_limit_parameter_then_extracts_limit(self):
        expected_result = {'limit': 532}
        args = {'limit': '532'}

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))

    def test_given_direction_parameter_then_extracts_direction(self):
        expected_result = {'direction': 'asc'}
        args = {'direction': 'asc'}

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))

    def test_given_invalid_direction_parameter_then_raises_error(self):
        args = {'direction': 'yeehaw'}

        self.assertRaises(InputError, extract_search_parameters, args)

    def test_given_search_parameter_then_extracts_search_term(self):
        expected_result = {'search': 'abcd'}
        args = {'search': 'abcd'}

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))

    def test_given_order_parameter_then_extracts_order_parameter(self):
        expected_result = {'order': 'column_name'}
        args = {'order': 'column_name'}

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))

    def test_given_extra_parameters_then_extracts_extra_parameters(self):
        expected_result = {'extra': 'extravalue'}
        args = {'extra': 'extravalue'}
        extra_parameters = ['extra']

        parameters = extract_search_parameters(args, extra=extra_parameters)

        assert_that(parameters, equal_to(expected_result))

    def test_given_all_search_parameters_then_extracts_all_parameters(self):
        expected_result = {
            'skip': 532,
            'limit': 5432,
            'order': 'toto',
            'direction': 'asc',
            'search': 'abcd'
        }

        args = {
            'skip': '532',
            'limit': '5432',
            'order': 'toto',
            'direction': 'asc',
            'search': 'abcd'
        }

        parameters = extract_search_parameters(args)

        assert_that(parameters, equal_to(expected_result))
