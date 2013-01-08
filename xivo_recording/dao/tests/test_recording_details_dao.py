# -*- coding: UTF-8 -*-
#
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

import random
import unittest
from xivo_dao.alchemy import dbconnection
from xivo_recording.recording_config import RecordingConfig
from xivo_recording.dao.recording_details_dao import RecordingDetailsDao, \
    RecordingDetailsDbBinder


class TestRecordingDao(unittest.TestCase):
    '''
    Test pre-conditions:
    - an agent with id 2
    - a campaign with id 3
    - a type called call_dir_type and a table called recording in Asterisk database :

    CREATE TYPE call_dir_type AS ENUM
      ('incoming',
      'outgoing');
    ALTER TYPE call_dir_type
      OWNER TO asterisk;

    CREATE TABLE recording
    (
      cid character varying(32) NOT NULL,
      call_direction call_dir_type,
      start_time timestamp without time zone,
      end_time timestamp without time zone,
      caller character varying(32),
      client_id character varying(1024),
      callee character varying(32),
      filename character varying(1024),
      campaign_id integer NOT NULL,
      agent_id integer NOT NULL,
      CONSTRAINT recording_pkey PRIMARY KEY (cid ),
      CONSTRAINT recording_agent_id_fkey FOREIGN KEY (agent_id)
          REFERENCES agentfeatures (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION,
      CONSTRAINT recording_campaign_id_fkey FOREIGN KEY (campaign_id)
          REFERENCES record_campaign (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE NO ACTION
    )
    WITH (
      OIDS=FALSE
    );
    ALTER TABLE recording
      OWNER TO asterisk;

    '''

    def test_recording_db(self):

        cid = str(random.randint(10000, 99999999))
        call_direction = "incoming"
        start_time = "2004-10-19 10:23:54"
        end_time = "2004-10-19 10:23:56"
        caller = "+" + str(random.randint(1000, 9999))
        client_id = "satisfied client Žluťoučký kůň"
        campaign_id = 3

        expected_dir = {"cid": cid,
                        "campaign_id": campaign_id,
                        "call_direction": call_direction,
                        "start_time": start_time,
                        "end_time": end_time,
                        "caller": caller,
                        "client_id": client_id,
                        "agent_id": 2
                        }

        expected_object = RecordingDetailsDao()
        for k, v in expected_dir.items():
            setattr(expected_object, k, v)

        dbconnection.unregister_db_connection_pool()
        dbconnection.register_db_connection_pool(dbconnection.DBConnectionPool(dbconnection.DBConnection))
        dbconnection.add_connection(RecordingConfig.RECORDING_DB_URI)

        record_db = RecordingDetailsDbBinder.new_from_uri(RecordingConfig.RECORDING_DB_URI)
        record_db.add_recording(expected_dir)
        records = record_db.get_records()

        print("read from database:")
        for record in records:
            print(record.to_string())

        print("saved:")
        print(expected_object.to_string())

        self.assert_(expected_object in records,
                     "Write/read from database failed")