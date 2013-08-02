# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launchpadlib import launchpad
import mock
from oslo.config import cfg
import testtools

from stackalytics.processor import persistent_storage
from stackalytics.processor import record_processor
from stackalytics.processor import utils


class TestRecordProcessor(testtools.TestCase):
    def setUp(self):
        super(TestRecordProcessor, self).setUp()

        companies = [
            {
                'company_name': 'SuperCompany',
                'domains': ['super.com', 'super.no']
            },
            {
                "domains": ["nec.com", "nec.co.jp"],
                "company_name": "NEC"
            },
            {
                'company_name': '*independent',
                'domains': ['']
            },
        ]

        self.user = {
            'user_id': 'john_doe',
            'launchpad_id': 'john_doe',
            'user_name': 'John Doe',
            'emails': ['johndoe@gmail.com', 'jdoe@super.no'],
            'companies': [
                {'company_name': '*independent',
                 'end_date': 1234567890},
                {'company_name': 'SuperCompany',
                 'end_date': 0},
            ]
        }
        self.get_users = mock.Mock(return_value=[
            self.user,
        ])

        releases = [
            {
                'release_name': 'prehistory',
                'end_date': utils.date_to_timestamp('2011-Apr-21')
            },
            {
                'release_name': 'Diablo',
                'end_date': utils.date_to_timestamp('2011-Sep-08')
            },
        ]

        def find(table, **criteria):
            if table == 'companies':
                return companies
            elif table == 'users':
                return self.get_users()
            elif table == 'releases':
                return releases
            else:
                raise Exception('Wrong table %s' % table)

        p_storage = mock.Mock(persistent_storage.PersistentStorage)
        p_storage.find = mock.Mock(side_effect=find)

        self.persistent_storage = p_storage
        self.commit_processor = record_processor.RecordProcessor(p_storage)
        self.launchpad_patch = mock.patch('launchpadlib.launchpad.Launchpad')
        self.launchpad_patch.start()
        cfg.CONF = mock.MagicMock()

    def tearDown(self):
        super(TestRecordProcessor, self).tearDown()
        self.launchpad_patch.stop()

    def _make_commit(self, email='johndoe@gmail.com', date=1999999999):
        return {
            'author_name': 'John Doe',
            'author_email': email,
            'date': date,
        }

    def test_get_company_by_email_mapped(self):
        email = 'jdoe@super.no'
        res = self.commit_processor._get_company_by_email(email)
        self.assertEquals('SuperCompany', res)

    def test_get_company_by_email_with_long_suffix_mapped(self):
        email = 'man@mxw.nes.nec.co.jp'
        res = self.commit_processor._get_company_by_email(email)
        self.assertEquals('NEC', res)

    def test_get_company_by_email_with_long_suffix_mapped_2(self):
        email = 'man@mxw.nes.nec.com'
        res = self.commit_processor._get_company_by_email(email)
        self.assertEquals('NEC', res)

    def test_get_company_by_email_not_mapped(self):
        email = 'foo@boo.com'
        res = self.commit_processor._get_company_by_email(email)
        self.assertEquals(None, res)

    def test_update_commit_existing_user(self):
        commit = self._make_commit()
        self.commit_processor._update_record_and_user(commit)

        self.assertEquals('SuperCompany', commit['company_name'])
        self.assertEquals('john_doe', commit['launchpad_id'])

    def test_update_commit_existing_user_old_job(self):
        commit = self._make_commit(date=1000000000)
        self.commit_processor._update_record_and_user(commit)

        self.assertEquals('*independent', commit['company_name'])
        self.assertEquals('john_doe', commit['launchpad_id'])

    def test_update_commit_existing_user_new_email_known_company(self):
        """
        User is known to LP, his email is new to us, and maps to other company
        Should return other company instead of those mentioned in user db
        """
        email = 'johndoe@nec.co.jp'
        commit = self._make_commit(email=email)
        lp_mock = mock.MagicMock()
        launchpad.Launchpad.login_anonymously = mock.Mock(return_value=lp_mock)
        lp_profile = mock.Mock()
        lp_profile.name = 'john_doe'
        lp_mock.people.getByEmail = mock.Mock(return_value=lp_profile)
        user = self.user.copy()
        # tell storage to return existing user
        self.get_users.return_value = [user]

        self.commit_processor._update_record_and_user(commit)

        self.persistent_storage.update.assert_called_once_with('users', user)
        lp_mock.people.getByEmail.assert_called_once_with(email=email)
        self.assertIn(email, user['emails'])
        self.assertEquals('NEC', commit['company_name'])
        self.assertEquals('john_doe', commit['launchpad_id'])

    def test_update_commit_existing_user_new_email_unknown_company(self):
        """
        User is known to LP, but his email is new to us. Should match
        the user and return current company
        """
        email = 'johndoe@yahoo.com'
        commit = self._make_commit(email=email)
        lp_mock = mock.MagicMock()
        launchpad.Launchpad.login_anonymously = mock.Mock(return_value=lp_mock)
        lp_profile = mock.Mock()
        lp_profile.name = 'john_doe'
        lp_mock.people.getByEmail = mock.Mock(return_value=lp_profile)
        user = self.user.copy()
        # tell storage to return existing user
        self.get_users.return_value = [user]

        self.commit_processor._update_record_and_user(commit)

        self.persistent_storage.update.assert_called_once_with('users', user)
        lp_mock.people.getByEmail.assert_called_once_with(email=email)
        self.assertIn(email, user['emails'])
        self.assertEquals('SuperCompany', commit['company_name'])
        self.assertEquals('john_doe', commit['launchpad_id'])

    def test_update_commit_new_user(self):
        """
        User is known to LP, but new to us
        Should add new user and set company depending on email
        """
        email = 'smith@nec.com'
        commit = self._make_commit(email=email)
        lp_mock = mock.MagicMock()
        launchpad.Launchpad.login_anonymously = mock.Mock(return_value=lp_mock)
        lp_profile = mock.Mock()
        lp_profile.name = 'smith'
        lp_profile.display_name = 'Smith'
        lp_mock.people.getByEmail = mock.Mock(return_value=lp_profile)
        self.get_users.return_value = []

        self.commit_processor._update_record_and_user(commit)

        lp_mock.people.getByEmail.assert_called_once_with(email=email)
        self.assertEquals('NEC', commit['company_name'])
        self.assertEquals('smith', commit['launchpad_id'])

    def test_update_commit_new_user_unknown_to_lb(self):
        """
        User is new to us and not known to LP
        Should set user name and empty LPid
        """
        email = 'inkognito@avs.com'
        commit = self._make_commit(email=email)
        lp_mock = mock.MagicMock()
        launchpad.Launchpad.login_anonymously = mock.Mock(return_value=lp_mock)
        lp_mock.people.getByEmail = mock.Mock(return_value=None)
        self.get_users.return_value = []

        self.commit_processor._update_record_and_user(commit)

        lp_mock.people.getByEmail.assert_called_once_with(email=email)
        self.assertEquals('*independent', commit['company_name'])
        self.assertEquals(None, commit['launchpad_id'])

    def test_update_commit_new_user_lb_raises_error(self):
        """
        LP raises error during getting user info
        """
        email = 'smith@avs.com'
        commit = self._make_commit(email=email)
        lp_mock = mock.MagicMock()
        launchpad.Launchpad.login_anonymously = mock.Mock(return_value=lp_mock)
        lp_mock.people.getByEmail = mock.Mock(return_value=None,
                                              side_effect=Exception)
        self.get_users.return_value = []

        self.commit_processor._update_record_and_user(commit)

        lp_mock.people.getByEmail.assert_called_once_with(email=email)
        self.assertEquals('*independent', commit['company_name'])
        self.assertEquals(None, commit['launchpad_id'])

    def test_update_commit_invalid_email(self):
        """
        User's email is malformed
        """
        email = 'error.root'
        commit = self._make_commit(email=email)
        lp_mock = mock.MagicMock()
        launchpad.Launchpad.login_anonymously = mock.Mock(return_value=lp_mock)
        lp_mock.people.getByEmail = mock.Mock(return_value=None)
        self.get_users.return_value = []

        self.commit_processor._update_record_and_user(commit)

        self.assertEquals(0, lp_mock.people.getByEmail.called)
        self.assertEquals('*independent', commit['company_name'])
        self.assertEquals(None, commit['launchpad_id'])
