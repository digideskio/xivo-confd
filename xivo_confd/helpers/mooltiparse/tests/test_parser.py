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

import unittest
from mock import Mock
from hamcrest import assert_that, equal_to, instance_of, contains

from xivo_confd.helpers.mooltiparse.field import Field
from xivo_confd.helpers.mooltiparse.document import Document, DocumentProxy
from xivo_confd.helpers.mooltiparse.registry import ParserRegistry
from xivo_confd.helpers.mooltiparse.parser import Parser
from xivo_confd.helpers.mooltiparse.errors import ContentTypeError


class TestParser(unittest.TestCase):

    def setUp(self):
        self.registry = Mock(ParserRegistry)
        self.parser = Parser(self.registry)

    def test_given_a_request_then_extracts_and_returns_parsed_content(self):
        content_type = 'application/json'
        request = Mock(mimetype=content_type)
        content = request.data = Mock()
        document = Mock(Document)
        parser = self.registry.parser_for_content_type.return_value = Mock()
        parsed_content = parser.return_value

        result = self.parser.parse(request, document)

        self.registry.parser_for_content_type.assert_called_once_with(content_type)
        parser.assert_called_once_with(content, document)

        assert_that(result, equal_to(parsed_content))

    def test_given_a_request_with_option_then_extracts_only_mimetype(self):
        content_type = 'application/json'
        content_type_with_option = '{content_type}; charset=UTF-8'.format(content_type=content_type)
        request = Mock(mimetype=content_type, headers={'Content-Type': content_type_with_option})
        content = request.data = Mock()
        document = Mock(Document)
        parser = self.registry.parser_for_content_type.return_value = Mock()
        parsed_content = parser.return_value

        result = self.parser.parse(request, document)

        self.registry.parser_for_content_type.assert_called_once_with(content_type)
        parser.assert_called_once_with(content, document)

        assert_that(result, equal_to(parsed_content))

    def test_given_no_content_type_then_raises_error(self):
        request = Mock(mimetype='', data=None)

        self.assertRaises(ContentTypeError, self.parser.parse, request, Mock())

    def test_given_a_document_and_action_then_validates_document(self):
        request = Mock()
        document = Mock(Document)
        parser = self.registry.parser_for_content_type.return_value = Mock()
        parsed_content = parser.return_value
        action = 'action'

        self.parser.parse(request, document, action)

        document.validate.assert_called_once_with(parsed_content, action)

    def test_given_a_list_of_fields_then_returns_a_document_proxy(self):
        field1 = Mock(Field)
        field2 = Mock(Field)

        result = self.parser.document(field1, field2)
        assert_that(result, instance_of(DocumentProxy))
        assert_that(result.document.fields, contains(field1, field2))

    def test_given_a_custom_content_parser_when_registered_then_added_to_the_registry(self):
        content_parser = Mock()

        self.parser.content_parser('custom/type')(content_parser)

        self.registry.register.assert_called_once_with('custom/type', content_parser)
