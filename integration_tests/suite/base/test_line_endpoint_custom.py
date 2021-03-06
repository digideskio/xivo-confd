# -*- coding: UTF-8 -*-

# Copyright (C) 2016 Avencall
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

from hamcrest import assert_that, has_entries

from test_api import scenarios as s
from test_api import confd
from test_api import errors as e
from test_api import helpers as h
from test_api import fixtures
from test_api import associations as a


@fixtures.line()
@fixtures.custom()
def test_associate_errors(line, custom):
    fake_line = confd.lines(999999999).endpoints.custom(custom['id']).put
    fake_custom = confd.lines(line['id']).endpoints.custom(999999999).put

    yield s.check_resource_not_found, fake_line, 'Line'
    yield s.check_resource_not_found, fake_custom, 'CustomEndpoint'


@fixtures.line()
@fixtures.custom()
def test_dissociate_errors(line, custom):
    fake_line = confd.lines(999999999).endpoints.custom(custom['id']).delete
    fake_custom = confd.lines(line['id']).endpoints.custom(999999999).delete

    yield s.check_resource_not_found, fake_line, 'Line'
    yield s.check_resource_not_found, fake_custom, 'CustomEndpoint'


def test_get_errors():
    fake_line = confd.lines(999999999).endpoints.custom.get
    fake_custom = confd.endpoints.custom(999999999).lines.get

    yield s.check_resource_not_found, fake_line, 'Line'
    yield s.check_resource_not_found, fake_custom, 'CustomEndpoint'


@fixtures.line()
@fixtures.custom()
def test_get_custom_endpoint_associated_to_line(line, custom):
    response = confd.lines(line['id']).endpoints.custom.get()
    response.assert_status(404)

    with a.line_endpoint_custom(line, custom):
        response = confd.lines(line['id']).endpoints.custom.get()
        assert_that(response.item, has_entries({'line_id': line['id'],
                                                'endpoint_id': custom['id'],
                                                'endpoint': 'custom'}))


@fixtures.line()
@fixtures.custom()
def test_get_custom_endpoint_after_dissociation(line, custom):
    h.line_endpoint_custom.associate(line['id'], custom['id'])
    h.line_endpoint_custom.dissociate(line['id'], custom['id'])

    response = confd.lines(line['id']).endpoints.custom.get()
    response.assert_status(404)


@fixtures.line()
@fixtures.custom()
def test_get_line_associated_to_a_custom_endpoint(line, custom):
    response = confd.endpoints.custom(custom['id']).lines.get()
    response.assert_status(404)

    with a.line_endpoint_custom(line, custom):
        response = confd.endpoints.custom(custom['id']).lines.get()
        assert_that(response.item, has_entries({'line_id': line['id'],
                                                'endpoint_id': custom['id'],
                                                'endpoint': 'custom'}))


@fixtures.line()
@fixtures.custom()
def test_associate(line, custom):
    response = confd.lines(line['id']).endpoints.custom(custom['id']).put()
    response.assert_updated()


@fixtures.line()
@fixtures.custom()
def test_associate_when_endpoint_already_associated(line, custom):
    with a.line_endpoint_custom(line, custom):
        response = confd.lines(line['id']).endpoints.custom(custom['id']).put()
        response.assert_match(400, e.resource_associated('Line', 'Endpoint'))


@fixtures.line()
@fixtures.custom()
@fixtures.custom()
def test_associate_with_another_endpoint_when_already_associated(line, custom1, custom2):
    with a.line_endpoint_custom(line, custom1):
        response = confd.lines(line['id']).endpoints.custom(custom2['id']).put()
        response.assert_match(400, e.resource_associated('Line', 'Endpoint'))


@fixtures.line()
@fixtures.custom()
def test_dissociate(line, custom):
    with a.line_endpoint_custom(line, custom, check=False):
        response = confd.lines(line['id']).endpoints.custom(custom['id']).delete()
        response.assert_deleted()


@fixtures.line()
@fixtures.custom()
def test_dissociate_when_not_associated(line, custom):
    response = confd.lines(line['id']).endpoints.custom(custom['id']).delete()
    response.assert_status(400)


@fixtures.line()
@fixtures.custom()
@fixtures.user()
def test_dissociate_when_associated_to_user(line, custom, user):
    with a.line_endpoint_custom(line, custom), a.user_line(user, line):
        response = confd.lines(line['id']).endpoints.custom(custom['id']).delete()
        response.assert_match(400, e.resource_associated('Line', 'User'))


@fixtures.line()
@fixtures.custom()
@fixtures.extension()
def test_dissociate_when_associated_to_extension(line, custom, extension):
    with a.line_endpoint_custom(line, custom), a.line_extension(line, extension):
        response = confd.lines(line['id']).endpoints.custom(custom['id']).delete()
        response.assert_match(400, e.resource_associated('Line', 'Extension'))


@fixtures.line()
@fixtures.custom()
def test_delete_endpoint_dissociates_line(line, custom):
    with a.line_endpoint_custom(line, custom, check=False):
        response = confd.endpoints.custom(custom['id']).delete()
        response.assert_deleted()

        response = confd.lines(line['id']).endpoints.custom.get()
        response.assert_status(404)
