
from test_api import scenarios as s
from test_api import helpers as h
from test_api import errors as e
from test_api import associations as a
from test_api import confd
from test_api import fixtures

from hamcrest import assert_that, has_entries, has_items
FAKE_ID = 999999999


class TestUserVoicemailAssociation(s.AssociationScenarios,
                                   s.DissociationScenarios,
                                   s.AssociationGetScenarios):

    left_resource = "User"
    right_resource = "Voicemail"

    def create_resources(self):
        self.user_id = h.user.generate_user()['id']
        self.voicemail_id = h.voicemail.generate_voicemail()['id']
        return self.user_id, self.voicemail_id

    def delete_resources(self, user_id, voicemail_id):
        h.voicemail.delete_voicemail(self.voicemail_id)
        h.user.delete_user(self.user_id)
        h.voicemail.delete_voicemail(self.voicemail_id)

    def associate_resources(self, user_id, voicemail_id):
        return confd.users(user_id).voicemail.post(voicemail_id=voicemail_id)

    def dissociate_resources(self, user_id, voicemail_id):
        return confd.users(user_id).voicemail.delete()

    def get_association(self, user_id, voicemail_id):
        return confd.users(user_id).voicemail.get()


@fixtures.user()
@fixtures.voicemail()
def test_associate(user, voicemail):
    response = confd.users(user['id']).voicemail.post(voicemail_id=voicemail['id'])
    response.assert_created('users', 'voicemail')


@fixtures.user()
@fixtures.voicemail()
def test_associate_using_uuid(user, voicemail):
    response = confd.users(user['uuid']).voicemail.post(voicemail_id=voicemail['id'])
    response.assert_created('users', 'voicemail')


@fixtures.user()
@fixtures.voicemail()
def test_associate_when_already_associated(user, voicemail):
    with a.user_voicemail(user, voicemail):
        response = confd.users(user['id']).voicemail.post(voicemail_id=voicemail['id'])
        response.assert_match(400, e.resource_associated('User', 'Voicemail'))


@fixtures.user()
@fixtures.user()
@fixtures.voicemail()
def test_associate_multiple_users_to_voicemail(user1, user2, voicemail):
    response = confd.users(user1['id']).voicemail.post(voicemail_id=voicemail['id'])
    response.assert_created('users', 'voicemail')

    response = confd.users(user2['id']).voicemail.post(voicemail_id=voicemail['id'])
    response.assert_created('users', 'voicemail')


@fixtures.user()
def test_get_when_not_associated(user):
    response = confd.users(user['id']).voicemail.get()
    response.assert_match(404, e.not_found('UserVoicemail'))


@fixtures.user()
@fixtures.voicemail()
def test_get_user_voicemail_association(user, voicemail):
    expected = has_entries({'user_id': user['id'],
                            'voicemail_id': voicemail['id']})

    with a.user_voicemail(user, voicemail):
        response = confd.users(user['id']).voicemail.get()
        assert_that(response.item, expected)

        response = confd.users(user['uuid']).voicemail.get()
        assert_that(response.item, expected)


@fixtures.user()
@fixtures.voicemail()
def test_get_user_voicemail_after_dissociation(user, voicemail):
    h.user_voicemail.associate(user['id'], voicemail['id'])
    h.user_voicemail.dissociate(user['id'], voicemail['id'])

    response = confd.users(user['id']).voicemail.get()
    response.assert_match(404, e.not_found('UserVoicemail'))

    response = confd.users(user['uuid']).voicemail.get()
    response.assert_match(404, e.not_found('UserVoicemail'))


@fixtures.user()
@fixtures.voicemail()
def test_dissociate(user, voicemail):
    with a.user_voicemail(user, voicemail, check=False):
        response = confd.users(user['id']).voicemail.delete()
        response.assert_deleted()


@fixtures.user()
@fixtures.voicemail()
def test_dissociate_using_uuid(user, voicemail):
    with a.user_voicemail(user, voicemail, check=False):
        response = confd.users(user['uuid']).voicemail.delete()
        response.assert_deleted()


@fixtures.user()
def test_dissociate_when_not_associated(user):
    response = confd.users(user['id']).voicemail.delete()
    response.assert_match(404, e.not_found('UserVoicemail'))


@fixtures.user()
@fixtures.voicemail()
def test_delete_user_when_still_associated(user, voicemail):
    with a.user_voicemail(user, voicemail):
        response = confd.users(user['id']).delete()
        response.assert_match(400, e.resource_associated('User', 'Voicemail'))


@fixtures.user()
@fixtures.voicemail()
def test_delete_voicemail_when_still_associated(user, voicemail):
    with a.user_voicemail(user, voicemail):
        response = confd.voicemails(voicemail['id']).delete()
        response.assert_match(400, e.resource_associated('Voicemail', 'User'))


@fixtures.user()
@fixtures.voicemail()
def test_edit_voicemail_when_still_associated(user, voicemail):
    number = h.voicemail.find_available_number(voicemail['context'])
    with a.user_voicemail(user, voicemail):
        response = confd.voicemails(voicemail['id']).put(number=number)
        response.assert_updated()


def test_get_users_associated_to_voicemail_when_voicemail_does_not_exist():
    response = confd.voicemails(FAKE_ID).users.get()
    response.assert_match(404, e.not_found('Voicemail'))


@fixtures.user()
@fixtures.user()
@fixtures.voicemail()
def test_get_multiple_users_associated_to_voicemail(user1, user2, voicemail):
    expected = has_items(
        has_entries({'user_id': user1['id'],
                     'voicemail_id': voicemail['id']}),
        has_entries({'user_id': user2['id'],
                     'voicemail_id': voicemail['id']}))

    with a.user_voicemail(user1, voicemail), a.user_voicemail(user2, voicemail):
        response = confd.voicemails(voicemail['id']).users.get()
        assert_that(response.items, expected)
