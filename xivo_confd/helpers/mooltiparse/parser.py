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

from document import Document, DocumentProxy
from errors import ContentTypeError


class Parser(object):

    def __init__(self, registry):
        self.registry = registry

    def parse(self, request, document, action=None):
        content, content_type = self._extract_from_request(request)
        parser = self.registry.parser_for_content_type(content_type)
        parsed = parser(content, document)
        document.validate(parsed, action)
        return parsed

    def _extract_from_request(self, request):
        content_type = request.mimetype
        content = request.data

        if not content_type:
            raise ContentTypeError('Content-Type required')

        return content, content_type

    def document(self, *fields):
        document = Document(fields)
        return DocumentProxy(self, document)

    def content_parser(self, content_type):
        def wrapper(func):
            self.registry.register(content_type, func)
            return func
        return wrapper
