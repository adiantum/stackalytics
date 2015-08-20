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

# Read data from zanata.openstack.org

import re
from oslo_log import log as logging

ZANATA_URI = r'https://zanata.openstack.org'

LOG = logging.getLogger(__name__)

class Tls(object):
    def __init__(self):
        pass

    def get_project_list(self):
        pass

    def log(self, user_id ):
        return []

class ZanataService(Tls):
    def __init__(self, uri):
        pass

    def get_project_list(self):
        pass

    # Return a translation record for a project
    def log(self, user_id ):
        #get user contribution from each project
        #yield translation
        return []


def get_tls(uri):
    LOG.debug('Translation tool is requested for uri %s' % uri)
    match = re.search(ZANATA_URI, uri)
    if match:
        return ZanataService(uri)
    else:
        LOG.warning('Unsupported translation tool, fallback to dummy')
        return Tls()