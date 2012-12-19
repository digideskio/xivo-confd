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
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..

from acceptance.features.rest_queues import RestQueues
from lettuce import step

restqueues = RestQueues()

@step(u'When I create a queue "([^"]*)"')
def when_i_create_a_queue(step, group1):
    global restqueues 
    assert restqueues.create("test_lettuce")
    
@step(u'Then I can consult this queue')
def then_i_can_consult_this_queue(step):
    global restqueues 
    assert restqueues.list("name", "test_lettuce")
    