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

from hamcrest import (assert_that,
                      contains,
                      empty,
                      has_entries,
                      not_)

from test_api import scenarios as s
from test_api import confd
from test_api import errors as e
from test_api import helpers as h
from test_api import fixtures
from test_api import associations as a


FAKE_ID = 999999999


@fixtures.user()
@fixtures.call_permission()
def test_associate_errors(user, call_permission):
    fake_user = confd.users(FAKE_ID).callpermissions(call_permission['id']).put
    fake_call_permission = confd.users(user['id']).callpermissions(FAKE_ID).put

    yield s.check_resource_not_found, fake_user, 'User'
    yield s.check_resource_not_found, fake_call_permission, 'CallPermission'


@fixtures.user()
@fixtures.call_permission()
def test_dissociate_errors(user, call_permission):
    fake_user_call_permission = confd.users(user['id']).callpermissions(call_permission['id']).delete
    fake_user = confd.users(FAKE_ID).callpermissions(call_permission['id']).delete
    fake_call_permission = confd.users(user['id']).callpermissions(FAKE_ID).delete

    yield s.check_resource_not_found, fake_user, 'User'
    yield s.check_resource_not_found, fake_call_permission, 'CallPermission'
    yield s.check_resource_not_found, fake_user_call_permission, 'UserCallPermission'


def test_get_errors():
    fake_user = confd.users(FAKE_ID).callpermissions.get
    fake_call_permission = confd.callpermissions(FAKE_ID).users.get

    yield s.check_resource_not_found, fake_user, 'User'
    yield s.check_resource_not_found, fake_call_permission, 'CallPermission'


@fixtures.user()
@fixtures.call_permission()
def test_associate_user_call_permission(user, call_permission):
    response = confd.users(user['id']).callpermissions(call_permission['id']).put()
    response.assert_updated()


@fixtures.user()
@fixtures.call_permission()
def test_associate_using_uuid(user, call_permission):
    response = confd.users(user['uuid']).callpermissions(call_permission['id']).put()
    response.assert_updated()


@fixtures.user()
@fixtures.call_permission()
@fixtures.call_permission()
@fixtures.call_permission()
def test_associate_multiple_call_permissions_to_user(user, perm1, perm2, perm3):
    confd.users(user['id']).callpermissions(perm1['id']).put().assert_updated()
    confd.users(user['id']).callpermissions(perm2['id']).put().assert_updated()
    confd.users(user['id']).callpermissions(perm3['id']).put().assert_updated()


@fixtures.user()
@fixtures.user()
@fixtures.user()
@fixtures.call_permission()
def test_associate_multiple_users_to_call_permission(user1, user2, user3, call_permission):
    confd.users(user1['id']).callpermissions(call_permission['id']).put().assert_updated()
    confd.users(user2['id']).callpermissions(call_permission['id']).put().assert_updated()
    confd.users(user3['id']).callpermissions(call_permission['id']).put().assert_updated()


@fixtures.user()
@fixtures.call_permission()
@fixtures.call_permission()
def test_get_call_permissions_associated_to_user(user, perm1, perm2):
    expected = contains(has_entries({'user_id': user['id'],
                                     'call_permission_id': perm1['id']}),
                        has_entries({'user_id': user['id'],
                                     'call_permission_id': perm2['id']}))

    with a.user_call_permission(user, perm1):
        with a.user_call_permission(user, perm2):
            response = confd.users(user['id']).callpermissions.get()
            assert_that(response.items, expected)

            response = confd.users(user['uuid']).callpermissions.get()
            assert_that(response.items, expected)


@fixtures.user()
@fixtures.call_permission()
def test_get_call_permission_after_dissociation(user, call_permission):
    h.user_call_permission.associate(user['id'], call_permission['id'])
    h.user_call_permission.dissociate(user['id'], call_permission['id'])

    response = confd.users(user['id']).callpermissions.get()
    assert_that(response.items, empty())

    response = confd.users(user['uuid']).callpermissions.get()
    assert_that(response.items, empty())


@fixtures.user()
@fixtures.user()
@fixtures.call_permission()
def test_get_users_associated_to_call_permission(user1, user2, call_permission):
    expected = contains(has_entries({'user_id': user1['id'],
                                     'call_permission_id': call_permission['id']}),
                        has_entries({'user_id': user2['id'],
                                     'call_permission_id': call_permission['id']}))

    with a.user_call_permission(user1, call_permission):
        with a.user_call_permission(user2, call_permission):
            response = confd.callpermissions(call_permission['id']).users.get()
            assert_that(response.items, expected)


@fixtures.user()
@fixtures.call_permission()
def test_associate_when_user_already_associated_to_same_call_permission(user, call_permission):
    with a.user_call_permission(user, call_permission):
        response = confd.users(user['id']).callpermissions(call_permission['id']).put()
        response.assert_match(400, e.resource_associated('User', 'CallPermission'))


@fixtures.user()
@fixtures.call_permission()
def test_dissociate_using_uuid(user, call_permission):
    with a.user_call_permission(user, call_permission, check=False):
        response = confd.users(user['uuid']).callpermissions(call_permission['id']).delete()
        response.assert_deleted()


@fixtures.user()
@fixtures.call_permission()
def test_delete_user_when_user_and_call_permission_associated(user, call_permission):
    with a.user_call_permission(user, call_permission, check=False):
        response = confd.users(user['id']).callpermissions.get()
        assert_that(response.items, not_(empty()))
        confd.users(user['id']).delete().assert_deleted()
        invalid_user = confd.users(user['id']).callpermissions.get
        yield s.check_resource_not_found, invalid_user, 'User'


@fixtures.user()
@fixtures.call_permission()
def test_delete_call_permission_when_user_and_call_permission_associated(user, call_permission):
    with a.user_call_permission(user, call_permission, check=False):
        response = confd.users(user['id']).callpermissions.get()
        assert_that(response.items, not_(empty()))
        confd.callpermissions(call_permission['id']).delete().assert_deleted()
        response = confd.users(user['id']).callpermissions.get()
        assert_that(response.items, empty())
