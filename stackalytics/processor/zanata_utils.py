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

import json
from oslo_log import log as logging
import random
import six
import yaml

from six.moves import http_client
from six.moves.urllib import parse

from stackalytics.processor import utils

LOG = logging.getLogger(__name__)

ZANATA_URI = 'https://translate-dev.openstack.org/rest/%s'
DATA_FORMAT = "%Y-%m-%d"

def zanata_get_projects():
	uri = ZANATA_URI % ('projects')
	LOG.debug("Reading projects from %s" % uri)
	projects_data = read_json_from_uri(uri)

	for project in projects_data:
		yield project

def zanata_get_project_locales(project_id, project_href):
	uri = ZANATA_URI % ('projects/%s/locales' % project_href)
	LOG.debug("Reading locales for project %s from %s" % (project_id, project_href))
	locales_data = read_json_from_uri(uri)

	for locale in locales_data:
		yield locale

def zanata_get_users(user_list_uri):
	return yaml.safe_load(utils.read_uri(user_list_uri))

def zanata_get_user_stats(project_id, iteration_id, zanata_user_id, 
						  start_date, end_date):
	start_date_str = start_date.strftime(DATA_FORMAT)
	end_date_str = end_date.strftime(DATA_FORMAT)
	uri = ZANATA_URI % ('stats/project/%s/version/%s/contributor/%s/%s..%s' 
						% (project_id, iteration_id, zanata_user_id, 
						   start_date_str, end_date_str))
	return read_json_from_uri(uri)


def read_uri(uri, headers):
    try:
    	headers['User-Agent'] = random.choice(utils.user_agents)
        req = six.moves.urllib.request.Request(
            url=uri, headers=headers)
        fd = six.moves.urllib.request.urlopen(req)
        raw = fd.read()
        fd.close()
        return raw
    except Exception as e:
        LOG.warn('Error "%(error)s" while reading uri %(uri)s',
                 {'error': e, 'uri': uri})


def read_json_from_uri(uri):
    try:
        return json.loads(read_uri(uri, {'Accept': 'application/json'}))
    except Exception as e:
        LOG.warn('Error "%(error)s" parsing json from uri %(uri)s',
                 {'error': e, 'uri': uri})