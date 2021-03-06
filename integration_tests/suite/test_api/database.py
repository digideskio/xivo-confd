# -*- coding: UTF-8 -*-

# Copyright (C) 2015-2016 Avencall
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

import os
import sqlalchemy as sa

from contextlib import contextmanager
from sqlalchemy.sql import text


class DbHelper(object):

    TEMPLATE = "xivotemplate"

    @classmethod
    def build(cls, user, password, host, port, db):
        tpl = "postgresql://{user}:{password}@{host}:{port}"
        uri = tpl.format(user=user,
                         password=password,
                         host=host,
                         port=port)
        return cls(uri, db)

    def __init__(self, uri, db):
        self.uri = uri
        self.db = db

    def create_engine(self, db=None, isolate=False):
        db = db or self.db
        uri = "{}/{}".format(self.uri, db)
        if isolate:
            return sa.create_engine(uri, isolation_level='AUTOCOMMIT')
        return sa.create_engine(uri)

    def connect(self, db=None):
        db = db or self.db
        return self.create_engine(db).connect()

    def recreate(self):
        engine = self.create_engine("postgres", isolate=True)
        connection = engine.connect()
        connection.execute("""
                           SELECT pg_terminate_backend(pg_stat_activity.pid)
                           FROM pg_stat_activity
                           WHERE pg_stat_activity.datname = '{db}'
                           AND pid <> pg_backend_pid()
                           """.format(db=self.db))
        connection.execute("DROP DATABASE IF EXISTS {db}".format(db=self.db))
        connection.execute("CREATE DATABASE {db} TEMPLATE {template}".format(db=self.db,
                                                                             template=self.TEMPLATE))
        connection.close()

    def execute(self, query, **kwargs):
        with self.connect() as connection:
            connection.execute(text(query), **kwargs)

    @contextmanager
    def queries(self):
        with self.connect() as connection:
            yield DatabaseQueries(connection)


class DatabaseQueries(object):

    def __init__(self, connection):
        self.connection = connection

    def insert_queue(self, name='myqueue', number='3000', context='default'):
        queue_query = text("""
        INSERT INTO queuefeatures (name, displayname, number, context)
        VALUES (:name, :displayname, :number, :context)
        RETURNING id
        """)

        queue_id = (self.connection
                    .execute(queue_query,
                             name=name,
                             displayname=name,
                             number=number,
                             context=context)
                    .scalar())

        self.insert_extension(number, context, 'queue', queue_id)

        func_key_id = self.insert_func_key('speeddial', 'queue')
        self.insert_destination('queue', 'queue_id', func_key_id, queue_id)

        return queue_id

    def insert_func_key(self, func_key_type, destination_type):
        func_key_query = text("""
        INSERT INTO func_key (type_id, destination_type_id)
        VALUES (
        (SELECT id FROM func_key_type WHERE name = :func_key_type),
        (SELECT id FROM func_key_destination_type WHERE name = :destination_type)
        )
        RETURNING id
        """)

        return (self.connection
                .execute(func_key_query,
                         func_key_type=func_key_type,
                         destination_type=destination_type)
                .scalar())

    def insert_destination(self, table, column, func_key_id, destination_id):
        destination_query = text("""
        INSERT INTO func_key_dest_{table} (func_key_id, {column})
        VALUES (:func_key_id, :destination_id)
        """.format(table=table, column=column))

        self.connection.execute(destination_query,
                                func_key_id=func_key_id,
                                destination_id=destination_id)

    def insert_conference(self, name='myconf', number='2000', context='default'):
        conf_query = text("""
        INSERT INTO meetmefeatures

        (meetmeid,
        name,
        confno,
        context,
        admin_identification,
        admin_mode,
        admin_announcejoinleave,
        user_mode,
        user_announcejoinleave,
        emailbody,
        description)

        VALUES

        (:meetmeid,
        :name,
        :confno,
        :context,
        :admin_identification,
        :admin_mode,
        :admin_announcejoinleave,
        :user_mode,
        :user_announcejoinleave,
        :emailbody,
        :description)

        RETURNING id
        """)

        conference_id = (self.connection
                         .execute(conf_query,
                                  meetmeid=1234,
                                  name=name,
                                  confno=number,
                                  context=context,
                                  admin_identification='pin',
                                  admin_mode='all',
                                  admin_announcejoinleave='no',
                                  user_mode='all',
                                  user_announcejoinleave='no',
                                  emailbody='email',
                                  description='')
                         .scalar())

        self.insert_extension(number, context, 'meetme', conference_id)

        func_key_id = self.insert_func_key('speeddial', 'conference')
        self.insert_destination('conference', 'conference_id', func_key_id, conference_id)

        return conference_id

    def insert_extension(self, exten, context, type_, typeval):
        exten_query = text("""
        INSERT INTO extensions (context, exten, type, typeval)
        VALUES (:context, :exten, :type, :typeval)
        RETURNING id
        """)

        return (self.connection
                .execute(exten_query,
                         context=context,
                         exten=exten,
                         type=type_,
                         typeval=str(typeval))
                .scalar())

    def insert_group(self, name='mygroup', number='1234', context='default'):
        query = text("""
        INSERT INTO groupfeatures (name, number, context)
        VALUES (:name, :number, :context)
        RETURNING id
        """)

        group_id = (self.connection
                    .execute(query,
                             name=name,
                             number=number,
                             context=context)
                    .scalar())

        self.insert_extension(number, context, 'group', group_id)

        func_key_id = self.insert_func_key('speeddial', 'group')
        self.insert_destination('group', 'group_id', func_key_id, group_id)

        return group_id

    def insert_agent(self, number='1000', context='default'):
        query = text("""
        INSERT INTO agentfeatures
        (numgroup, number, passwd, context, language, description)
        VALUES (
            (SELECT groupid FROM agentgroup WHERE name = :context),
            :number,
            '',
            :context,
            '',
            ''
        )
        RETURNING id
        """)

        func_key_query = text("""
        INSERT INTO func_key_dest_agent (func_key_id, agent_id, extension_id)
        VALUES (
        :func_key_id,
        :agent_id,
        (SELECT id FROM extensions WHERE type = 'extenfeatures' AND typeval = :typeval)
        )
        """)

        agent_id = (self.connection
                    .execute(query,
                             number=number,
                             context=context)
                    .scalar())

        func_key_id = self.insert_func_key('speeddial', 'agent')

        for typeval in ('agentstaticlogin', 'agentstaticlogoff', 'agentstaticlogtoggle'):
            func_key_id = self.insert_func_key('speeddial', 'agent')
            self.connection.execute(func_key_query,
                                    func_key_id=func_key_id,
                                    agent_id=agent_id,
                                    typeval=typeval)

        return agent_id

    def insert_paging(self, number='1234'):
        query = text("""
        INSERT INTO paging (number, timeout)
        VALUES (:number, :timeout)
        RETURNING id
        """)

        paging_id = (self.connection
                     .execute(query,
                              number=number,
                              timeout=30)
                     .scalar())

        func_key_id = self.insert_func_key('speeddial', 'paging')
        self.insert_destination('paging', 'paging_id', func_key_id, paging_id)

        return paging_id

    def insert_callfilter(self, name='bsfilter', type_='bosssecretary', bosssecretary='secretary-simult'):
        query = text("""
        INSERT INTO callfilter (entity_id, name, type, bosssecretary, description)
        VALUES (
        (SELECT id FROM entity LIMIT 1),
        :name,
        :type,
        :bosssecretary,
        '')
        RETURNING id
        """)

        return (self.connection
                .execute(query,
                         name=name,
                         type=type_,
                         bosssecretary=bosssecretary)
                .scalar())

    def insert_filter_member(self, callfilter_id, member_id, bstype='secretary'):
        query = text("""
        INSERT INTO callfiltermember (callfilterid, type, typeval, bstype)
        VALUES (:callfilterid, :type, :typeval, :bstype)
        RETURNING id
        """)

        filter_member_id = (self.connection
                            .execute(query,
                                     callfilterid=callfilter_id,
                                     type='user',
                                     typeval=str(member_id),
                                     bstype=bstype)
                            .scalar())

        func_key_id = self.insert_func_key('speeddial', 'bsfilter')
        self.insert_destination('bsfilter', 'filtermember_id', func_key_id, filter_member_id)

        return filter_member_id

    def insert_context(self, **parameters):
        parameters.setdefault('displayname', parameters['name'])
        parameters.setdefault('description', '')
        parameters.setdefault('commented', 0)
        query = text("""
                     INSERT INTO context(name, displayname, contexttype, description, commented, entity)
                     VALUES (
                                :name, :displayname, :contexttype, :description, :commented,
                                (SELECT id FROM entity LIMIT 1)
                            )
                     """)

        self.connection.execute(query, **parameters)

        return parameters['name']

    def insert_context_range(self, context, type_, start, end, didlength=0):
        query = text("""
                     INSERT INTO contextnumbers(context, type, numberbeg, numberend, didlength)
                     VALUES (:context, :type, :numberbeg, :numberend, :didlength)
                     """)

        self.connection.execute(query, context=context, type=type_, numberbeg=start, numberend=end, didlength=didlength)

    def delete_context(self, name):
        query = text("DELETE FROM context WHERE name = :name")
        self.connection.execute(query, name=name)

    def insert_entity(self, name):
        query = text("""
        INSERT INTO entity (name, description)
        VALUES (:name, '')
        RETURNING id
        """)

        entity_id = (self.connection
                     .execute(query,
                              name=name)
                     .scalar())

        return entity_id

    def delete_entity(self, entity_id):
        query = text("DELETE FROM entity WHERE id = :id")
        self.connection.execute(query, id=entity_id)

    def get_entities(self):
        query = text("SELECT * FROM entity")
        return self.connection.execute(query)

    def associate_line_device(self, line_id, device_id):
        query = text("UPDATE linefeatures SET device = :device_id WHERE id = :line_id")
        self.connection.execute(query, device_id=device_id, line_id=line_id)

    def dissociate_line_device(self, line_id, device_id):
        query = text("UPDATE linefeatures SET device = NULL WHERE id = :line_id")
        self.connection.execute(query, device_id=device_id, line_id=line_id)

    def insert_switchboard(self, queue_id):
        query = text("""INSERT INTO stat_switchboard_queue(time, end_type, wait_time, queue_id)
                        VALUES ('2016-02-29 00:00:00', 'abandoned', 15.2, :queue_id)
                        RETURNING id""")
        return self.connection.execute(query, queue_id=queue_id).scalar()

    def find_queue(self, queue_name):
        query = text("""SELECT id from queuefeatures
                        WHERE name = :name""")
        return self.connection.execute(query, name=queue_name).first()

    def insert_switchboard_stat(self, time, end_type, wait_time, queue_id):
        query = text("""INSERT INTO stat_switchboard_queue(time, end_type, wait_time, queue_id)
                        VALUES (:time, :end_type, :wait_time, :queue_id)
                        RETURNING id""")
        return self.connection.execute(query,
                                       time=time,
                                       end_type=end_type,
                                       wait_time=wait_time,
                                       queue_id=queue_id).scalar()

    def delete_switchboard_stat(self, stat_id):
        query = text("""DELETE from stat_switchboard_queue
                        WHERE id = :id""")
        self.connection.execute(query, id=stat_id)

    def line_has_sccp_device(self, line_id, sccp_device):
        query = text("""SELECT COUNT(*)
                     FROM linefeatures
                        INNER JOIN sccpline
                            ON linefeatures.protocol = 'sccp'
                            AND linefeatures.protocolid = sccpline.id
                            INNER JOIN sccpdevice ON sccpdevice.line = linefeatures.number
                     WHERE
                        linefeatures.id = :line_id
                        AND sccpdevice.device = :sccp_device
                     """)

        count = (self.connection
                 .execute(query,
                          line_id=line_id,
                          sccp_device=sccp_device)
                 .scalar())

        return count > 0

    def admin_has_password(self, password):
        query = text("""SELECT COUNT(*)
                     FROM "user"
                     WHERE
                        login = 'root'
                        AND passwd = :password
                     """)
        count = (self.connection
                 .execute(query,
                          password=password)
                 .scalar())

        return count > 0

    def autoprov_is_configured(self):
        query = text("""SELECT COUNT(*)
                     FROM staticsip
                     WHERE
                        category = 'general'
                        AND filename = 'sip.conf'
                        AND var_name = 'autocreate_prefix'
                     """)
        count = (self.connection
                 .execute(query)
                 .scalar())

        return count > 0

    def entity_has_name_displayname(self, name, displayname):
        query = text("""SELECT COUNT(*)
                     FROM entity
                     WHERE
                        name = :name
                        AND displayname = :displayname
                     """)
        count = (self.connection
                 .execute(query,
                          name=name,
                          displayname=displayname)
                 .scalar())

        return count > 0

    def sip_has_language(self, language):
        query = text("""SELECT COUNT(*)
                     FROM staticsip
                     WHERE
                        var_name = 'language'
                        AND var_val = :language
                     """)
        count = (self.connection
                 .execute(query,
                          language=language)
                 .scalar())

        return count > 0

    def iax_has_language(self, language):
        query = text("""SELECT COUNT(*)
                     FROM staticiax
                     WHERE
                        var_name = 'language'
                        AND var_val = :language
                     """)
        count = (self.connection
                 .execute(query,
                          language=language)
                 .scalar())

        return count > 0

    def sccp_has_language(self, language):
        query = text("""SELECT COUNT(*)
                     FROM sccpgeneralsettings
                     WHERE
                        option_name = 'language'
                        AND option_value = :language
                     """)
        count = (self.connection
                 .execute(query,
                          language=language)
                 .scalar())

        return count > 0

    def general_has_timezone(self, timezone):
        query = text("""SELECT COUNT(*)
                     FROM general
                     WHERE
                        timezone = :timezone
                     """)
        count = (self.connection
                 .execute(query,
                          timezone=timezone)
                 .scalar())

        return count > 0

    def resolvconf_is_configured(self, hostname, domain, nameservers):
        query = text("""SELECT COUNT(*)
                     FROM resolvconf
                     WHERE
                        hostname = :hostname
                        AND domain = :domain
                        AND search = :domain
                        AND nameserver1 = :nameserver1
                        AND nameserver2 = :nameserver2
                     """)

        count = (self.connection
                 .execute(query,
                          hostname=hostname,
                          domain=domain,
                          nameserver1=nameservers[0],
                          nameserver2=nameservers[1])
                 .scalar())

        return count > 0

    def netiface_is_configured(self, address, gateway):
        # Note that interface and netmask are not tested
        query = text("""SELECT COUNT(*)
                     FROM netiface
                     WHERE
                        hwtypeid = 1
                        AND type = 'iface'
                        AND family = 'inet'
                        AND method = 'static'
                        AND address = :address
                        AND broadcast = ''
                        AND gateway = :gateway
                        AND mtu = 1500
                        AND options = ''
                     """)

        count = (self.connection
                 .execute(query,
                          address=address,
                          gateway=gateway)
                 .scalar())

        return count > 0

    def context_has_internal(self, display_name, number_start, number_end):
        query = text("""SELECT COUNT(*)
                     FROM context
                     INNER JOIN contextnumbers
                        ON context.name = contextnumbers.context
                     WHERE
                        context.name = 'default'
                        AND context.displayname = :display_name
                        AND context.contexttype = 'internal'
                        AND contextnumbers.type = 'user'
                        AND contextnumbers.numberbeg = :number_start
                        AND contextnumbers.numberend = :number_end
                        AND contextnumbers.didlength = 0
                     """)

        count = (self.connection
                 .execute(query,
                          display_name=display_name,
                          number_start=number_start,
                          number_end=number_end)
                 .scalar())

        return count > 0

    def context_has_incall(self, display_name=None, number_start=None, number_end=None, did_length=None):
        if number_start is None and number_end is None:
            query = text("""SELECT COUNT(*)
                         FROM context
                         WHERE
                            context.name = 'from-extern'
                            AND context.displayname = :display_name
                            AND context.contexttype = 'incall'
                         """)

            count = (self.connection
                     .execute(query,
                              display_name=display_name)
                     .scalar())
        else:
            query = text("""SELECT COUNT(*)
                         FROM context
                         INNER JOIN contextnumbers
                            ON context.name = contextnumbers.context
                         WHERE
                            context.name = 'from-extern'
                            AND context.displayname = :display_name
                            AND context.contexttype = 'incall'
                            AND contextnumbers.type = 'incall'
                            AND contextnumbers.numberbeg = :number_start
                            AND contextnumbers.numberend = :number_end
                            AND contextnumbers.didlength = :did_length
                         """)

            count = (self.connection
                     .execute(query,
                              display_name=display_name,
                              number_start=number_start,
                              number_end=number_end,
                              did_length=did_length)
                     .scalar())

        return count > 0

    def context_has_outcall(self, display_name):
        query = text("""SELECT COUNT(*)
                     FROM context
                     WHERE
                        context.name = 'to-extern'
                        AND context.displayname = :display_name
                        AND context.contexttype = 'outcall'
                     """)

        count = (self.connection
                 .execute(query,
                          display_name=display_name)
                 .scalar())

        return count > 0

    def context_has_switchboard(self):
        query = text("""SELECT COUNT(*)
                     FROM context
                     WHERE
                        context.name = '__switchboard_directory'
                        AND context.displayname = 'Switchboard'
                        AND context.contexttype = 'others'
                     """)

        count = (self.connection
                 .execute(query)
                 .scalar())

        return count > 0

    def internal_context_include_outcall_context(self):
        query = text("""SELECT COUNT(*)
                     FROM contextinclude
                     WHERE
                        context = 'default'
                        AND include = 'to-extern'
                        AND priority = 0
                     """)

        count = (self.connection
                 .execute(query)
                 .scalar())

        return count > 0


def create_helper():
    user = os.environ.get('DB_USER', 'asterisk')
    password = os.environ.get('DB_PASSORD', 'proformatique')
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', 15432)
    db = os.environ.get('DB_NAME', 'asterisk')

    return DbHelper.build(user, password, host, port, db)
