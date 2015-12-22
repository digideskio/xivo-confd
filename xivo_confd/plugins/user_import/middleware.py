# -*- coding: UTF-8 -*-

# Copyright (C) 2015 Avencall
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

import abc

from xivo_dao.helpers.db_manager import Session
from xivo_dao.helpers.exception import NotFoundError

from xivo_dao.alchemy.userfeatures import UserFeatures as User
from xivo_dao.alchemy.usersip import UserSIP as SIP
from xivo_dao.alchemy.sccpline import SCCPLine as SCCP
from xivo_dao.alchemy.dialaction import Dialaction
from xivo_dao.resources.voicemail.model import Voicemail

from xivo_dao.alchemy.linefeatures import LineFeatures as Line
from xivo_dao.resources.extension.model import Extension
from xivo_dao.resources.user_cti_profile.model import UserCtiProfile
from xivo_dao.resources.user_voicemail.model import UserVoicemail


class Creator(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, service):
        self.service = service

    @abc.abstractmethod
    def find(self, fields):
        pass

    @abc.abstractmethod
    def create(self, fields):
        pass

    def update(self, fields, model):
        self.update_model(fields, model)
        self.service.edit(model)

    def update_model(self, fields, model):
        for key, value in fields.iteritems():
            setattr(model, key, value)


class UserCreator(Creator):

    def find(self, fields):
        if 'uuid' in fields:
            return self.service.get_by(uuid=fields['uuid'])

    def create(self, fields):
        if fields:
            return self.service.create(User(**fields))


class VoicemailCreator(Creator):

    def find(self, fields):
        number = fields.get('number')
        context = fields.get('context')
        if number and context:
            try:
                return self.service.dao.get_by_number_context(number, context)
            except NotFoundError:
                return None

    def create(self, fields):
        if fields:
            return self.service.create(Voicemail(**fields))


class LineCreator(Creator):

    def find(self, fields):
        return None

    def update(self, fields, line):
        fields = dict(fields)
        if 'endpoint' in fields:
            del fields['endpoint']
            self.update_model(fields, line)
            self.service.edit(line)

    def create(self, fields):
        fields = dict(fields)
        endpoint = fields.pop('endpoint', None)
        if 'context' in fields and endpoint in ('sip', 'sccp'):
            return self.service.create(Line(**fields))


class SipCreator(Creator):

    def find(self, fields):
        name = fields.get('name')
        if name:
            return self.service.find_by(name=name)

    def create(self, fields):
        return self.service.create(SIP(**fields))


class SccpCreator(Creator):

    def find(self, fields):
        return None

    def create(self, fields):
        return self.service.create(SCCP(**fields))


class ExtensionCreator(Creator):

    def find(self, fields):
        exten = fields.get('exten')
        context = fields.get('context')
        if exten and context:
            try:
                return self.service.dao.get_by_exten_context(exten, context)
            except NotFoundError:
                return None

    def create(self, fields):
        if 'exten' in fields and 'context' in fields:
            return self.service.create(Extension(**fields))


class CtiProfileCreator(Creator):

    def __init__(self, dao):
        self.dao = dao

    def find(self, fields):
        name = fields.get('name')
        if name:
            try:
                cti_profile_id = self.dao.get_id_by_name(name)
                return self.dao.get(cti_profile_id)
            except NotFoundError:
                return None

    def update(self, fields, resource):
        pass

    def create(self, fields):
        if fields:
            cti_profile_id = self.dao.get_id_by_name(fields['name'])
            return self.dao.get(cti_profile_id)


class IncallCreator(Creator):

    def find(self, fields):
        exten = fields.get('exten')
        context = fields.get('context')
        if exten and context:
            try:
                return self.service.dao.get_by_exten_context(exten, context)
            except NotFoundError:
                return None

    def create(self, fields):
        fields = self.extract_extension_fields(fields)
        if fields:
            extension = Extension(**fields)
            return self.service.create(extension)

    def update(self, fields, resource):
        extension_fields = self.extract_extension_fields(fields)
        self.update_model(extension_fields, resource)
        self.service.edit(resource)

    def extract_extension_fields(self, fields):
        return {key: fields[key] for key in ('exten', 'context') if key in fields}


class Associator(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, service):
        self.service = service

    @abc.abstractmethod
    def associate(self, entry):
        return

    @abc.abstractmethod
    def update(self, entry):
        return


class LineAssociator(Associator):

    def associate(self, entry):
        user = entry.get_resource('user')
        line = entry.get_resource('line')
        if user and line:
            self.service.associate(user, line)

    def update(self, entry):
        user = entry.get_resource('user')
        line = entry.get_resource('line')
        if user and line and not self.associated(user, line):
            self.service.associate(user, line)

    def associated(self, user, line):
        return self.service.find_by(user_id=user.id, line_id=line.id) is not None


class ExtensionAssociator(Associator):

    def associate(self, entry):
        line = entry.get_resource('line')
        extension = entry.get_resource('extension')
        if line and extension:
            self.service.associate(line, extension)

    def update(self, entry):
        line = entry.get_resource('line')
        extension = entry.get_resource('extension')
        if line and extension and not self.associated(line, extension):
            self.service.associate(line, extension)

    def associated(self, line, extension):
        try:
            self.service.get(line, extension)
        except NotFoundError:
            return False
        return True


class SipAssociator(Associator):

    def associate(self, entry):
        line = entry.get_resource('line')
        sip = entry.get_resource('sip')
        if line and sip:
            self.service.associate(line, sip)

    def update(self, entry):
        line = entry.get_resource('line')
        sip = entry.get_resource('sip')
        if line and sip and not line.is_associated_with(sip):
                self.service.associate(line, sip)


class SccpAssociator(Associator):

    def associate(self, entry):
        line = entry.get_resource('line')
        sccp = entry.get_resource('sccp')
        if line and sccp:
            self.service.associate(line, sccp)

    def update(self, entry):
        line = entry.get_resource('line')
        sccp = entry.get_resource('sccp')
        if line and sccp and not line.is_associated_with(sccp):
                self.service.associate(line, sccp)


class VoicemailAssociator(Associator):

    def associate(self, entry):
        user = entry.get_resource('user')
        voicemail = entry.get_resource('voicemail')
        if user and voicemail:
            self.create_and_associate(user, voicemail)

    def create_and_associate(self, user, voicemail):
        association = UserVoicemail(user_id=user.id,
                                    voicemail_id=voicemail.id)
        self.service.associate(association)

    def update(self, entry):
        user = entry.get_resource('user')
        voicemail = entry.get_resource('voicemail')
        if user and voicemail and not self.associated(user, voicemail):
            self.create_and_associate(user, voicemail)

    def associated(self, user, voicemail):
        return self.service.find_by(user_id=user.id, voicemail_id=voicemail.id) is not None


class CtiProfileAssociator(Associator):

    def __init__(self, service, dao):
        self.service = service
        self.dao = dao

    def associate(self, entry):
        cti_profile = entry.get_resource('cti_profile')
        if cti_profile:
            self.associate_profile(entry)

    def update(self, entry):
        self.associate(entry)

    def associate_profile(self, entry):
        user = entry.get_resource('user')
        name = entry.extract_field('cti_profile', 'name')
        cti_profile_id = self.dao.get_id_by_name(name)
        association = UserCtiProfile(user_id=user.id,
                                     cti_profile_id=cti_profile_id,
                                     enabled=entry.extract_field('cti_profile', 'enabled'))
        self.service.edit(association)


class IncallAssociator(Associator):

    def associate(self, entry):
        line = entry.get_resource('line')
        incall = entry.get_resource('incall')
        if line and incall:
            self.service.associate(line, incall)
            self.update_ring_seconds(entry)

    def update_ring_seconds(self, entry):
        ring_seconds = entry.extract_field('incall', 'ring_seconds')
        if ring_seconds:
            user = entry.get_resource('user')
            (Session.query(Dialaction)
             .filter_by(event='answer',
                        category='incall',
                        action='user',
                        actionarg1=str(user.id))
             .update({'actionarg2': str(ring_seconds)}))

    def update(self, entry):
        line = entry.get_resource('line')
        incall = entry.get_resource('incall')
        if line and incall and not self.associated(line, incall):
            self.service.associate(line, incall)
            self.update_ring_seconds(entry)

    def associated(self, line, extension):
        try:
            self.service.get(line, extension)
        except NotFoundError:
            return False
        return True