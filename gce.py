# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from errbot import botcmd, BotPlugin
from datetime import datetime
from googleapiclient.discovery import build

def get_ts():
    now = datetime.now()
    return '%s.%d' % (now.strftime('%Y%m%d-%H%M%S'), now.microsecond)


class GoogleCloudCompute(BotPlugin):
    """This is a binding example from errbot to Google Cloud"""

    def activate(self):
        super().activate()
        self.gc = self.get_plugin('GoogleCloud')
        self.credentials = self.gc.credentials
        if not self.credentials:
            self.log.error('FATAL: GCloud plugin could not load credentials.')
            return

        self.compute = build('compute', 'v1', credentials=self.credentials)

    def project(self):
        if 'project' not in self.gc:
            raise Exception('No Project set.')
        return

    @botcmd(split_args_with=' ', template='vm')
    def vm_list(self, msg, args):
        """List VM instances in the given project and zone.
        """
        zone = 'us-central1-c'
        result = self.compute.instances().list(project=self.gc['project'], zone=zone).execute()
        yield {'vms': []} if 'items' not in result else {'vms': result['items']}


