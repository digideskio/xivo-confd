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

import string
import random

from test_api import db


def add_entity(name):
    with db.queries() as queries:
        id = queries.insert_entity(name)
    return {'id': id,
            'name': name}


def generate_entity(name=None):
    if name is None:
        name = generate_name()
    return add_entity(name)


def delete_entity(entity_id, check=False):
    with db.queries() as queries:
        queries.delete_entity(entity_id)


def generate_name():
    with db.queries() as queries:
        response = queries.get_entities()
    names = set(d['name'] for d in response)
    return _random_name(names)


def _random_name(names):
    name = ''.join(random.choice(string.lowercase) for i in range(10))
    while name in names:
        name = ''.join(random.choice(string.lowercase) for i in range(10))
    return name
