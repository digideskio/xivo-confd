# -*- coding: utf-8 -*-

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

import re

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import empty
from hamcrest import has_entries
from hamcrest import has_item

from test_api import scenarios as s
from test_api import confd
from test_api import errors as e
from test_api import helpers as h
from test_api import fixtures
from test_api import associations as a


secondary_user_regex = re.compile(r"There are secondary users associated to the line")

FAKE_ID = 999999999


@fixtures.user()
@fixtures.line_sip()
def test_associate_errors(user, line):
    fake_user = confd.users(FAKE_ID).lines(line_id=line['id']).post
    fake_line = confd.users(user['id']).lines(line_id=FAKE_ID).post

    yield s.check_resource_not_found, fake_user, 'User'
    yield s.check_bogus_field_returns_error, fake_line, 'line_id', FAKE_ID


@fixtures.user()
@fixtures.line_sip()
def test_dissociate_errors(user, line):
    fake_user = confd.users(FAKE_ID).lines(line['id']).delete
    fake_line = confd.users(user['id']).lines(FAKE_ID).delete

    yield s.check_resource_not_found, fake_user, 'User'
    yield s.check_resource_not_found, fake_line, 'Line'


def test_get_errors():
    fake_user = confd.users(FAKE_ID).lines.get
    fake_line = confd.lines(FAKE_ID).users.get

    yield s.check_resource_not_found, fake_user, 'User'
    yield s.check_resource_not_found, fake_line, 'Line'


@fixtures.user
@fixtures.line_sip
def test_associate_user_line(user, line):
    response = confd.users(user['id']).lines.put(line_id=line['id'])
    response.assert_updated()


@fixtures.user
@fixtures.line_sip
def test_associate_using_uuid(user, line):
    response = confd.users(user['uuid']).lines.put(line_id=line['id'])
    response.assert_updated()


@fixtures.user()
@fixtures.user()
@fixtures.user()
@fixtures.line_sip()
def test_associate_muliple_users_to_line(user1, user2, user3, line):
    response = confd.users(user1['id']).lines.post(line_id=line['id'])
    response.assert_created('users', 'lines')

    response = confd.users(user2['id']).lines.post(line_id=line['id'])
    response.assert_created('users', 'lines')

    response = confd.users(user3['id']).lines.post(line_id=line['id'])
    response.assert_created('users', 'lines')


@fixtures.user()
@fixtures.line_sip()
def test_get_line_associated_to_user(user, line):
    expected = contains(has_entries({'user_id': user['id'],
                                     'line_id': line['id'],
                                     'main_user': True,
                                     'main_line': True}))

    with a.user_line(user, line):
        response = confd.users(user['id']).lines.get()
        assert_that(response.items, expected)

        response = confd.users(user['uuid']).lines.get()
        assert_that(response.items, expected)


@fixtures.user()
@fixtures.line_sip()
def test_get_line_after_dissociation(user, line):
    h.user_line.associate(user['id'], line['id'])
    h.user_line.dissociate(user['id'], line['id'])

    response = confd.users(user['id']).lines.get()
    assert_that(response.items, empty())

    response = confd.users(user['uuid']).lines.get()
    assert_that(response.items, empty())


@fixtures.user()
@fixtures.line_sip()
def test_get_user_associated_to_line(user, line):
    expected = contains(has_entries({'user_id': user['id'],
                                     'line_id': line['id'],
                                     'main_user': True,
                                     'main_line': True}))

    with a.user_line(user, line):
        response = confd.lines(line['id']).users.get()
        assert_that(response.items, expected)


@fixtures.user()
@fixtures.user()
@fixtures.line_sip()
def test_get_secondary_user_associated_to_line(main_user, other_user, line):
    expected = has_item(has_entries({'user_id': other_user['id'],
                                     'line_id': line['id'],
                                     'main_user': False,
                                     'main_line': True}))

    with a.user_line(main_user, line), a.user_line(other_user, line):
        response = confd.lines(line['id']).users.get()
        assert_that(response.items, expected)


@fixtures.user()
@fixtures.line_sip()
def test_associate_when_user_already_associated_to_same_line(user, line):
    with a.user_line(user, line):
        response = confd.users(user['id']).lines.post(line_id=line['id'])
        response.assert_match(400, e.resource_associated('User', 'Line'))


@fixtures.user()
@fixtures.line_sip()
@fixtures.line_sip()
def test_associate_when_user_already_associated_to_another_line(user, first_line, second_line):
    with a.user_line(user, first_line):
        response = confd.users(user['id']).lines.post(line_id=first_line['id'])
        response.assert_match(400, e.resource_associated('User', 'Line'))


@fixtures.user()
@fixtures.line()
def test_associate_user_to_line_without_endpoint(user, line):
    response = confd.users(user['id']).lines.post(line_id=line['id'])
    response.assert_match(400, e.missing_association('Line', 'Endpoint'))


@fixtures.user()
@fixtures.line()
@fixtures.sip()
def test_associate_user_to_line_with_endpoint(user, line, sip):
    with a.line_endpoint_sip(line, sip, check=False):
        response = confd.users(user['id']).lines.post(line_id=line['id'])
        response.assert_created('users', 'lines')
        assert_that(response.item, has_entries({'user_id': user['id'],
                                                'line_id': line['id']}))


@fixtures.user()
@fixtures.line_sip()
def test_dissociate_using_uuid(user, line):
    with a.user_line(user, line, check=False):
        response = confd.users(user['uuid']).lines(line['id']).delete()
        response.assert_deleted()


@fixtures.user()
@fixtures.user()
@fixtures.line_sip()
def test_dissociate_second_user_then_first(first_user, second_user, line):
    with a.user_line(first_user, line, check=False), \
            a.user_line(second_user, line, check=False):
        response = confd.users(second_user['id']).lines(line['id']).delete()
        response.assert_deleted()

        response = confd.users(first_user['id']).lines(line['id']).delete()
        response.assert_deleted()


@fixtures.user()
@fixtures.user()
@fixtures.line_sip()
def test_dissociate_second_user_before_first(first_user, second_user, line):
    with a.user_line(first_user, line), a.user_line(second_user, line):
        response = confd.users(first_user['id']).lines(line['id']).delete()
        response.assert_match(400, secondary_user_regex)


@fixtures.user()
@fixtures.line_sip()
def test_delete_user_when_user_and_line_associated(user, line):
    with a.user_line(user, line):
        response = confd.users(user['id']).delete()
        response.assert_match(400, e.resource_associated('User', 'Line'))
