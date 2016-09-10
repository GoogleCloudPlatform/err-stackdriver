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

import logging
import os
import uuid

import requests
from errbot import BotPlugin, botcmd, cmdfilter, version
from googleapiclient.discovery import build
from matplotlib import use
from oauth2client.client import GoogleCredentials
from python_analytics import Tracker, Event
from threadpool import WorkRequest

use('Agg')


class GoogleCloud(BotPlugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.outdir = None
        self.credentials = None
        self.storage = None

    """This is a common common for Google Cloud plugins."""

    def activate(self):
        super().activate()
        self.outdir = self.bot_config.BOT_DATA_DIR
        # servacc.json is the service account credentials you can download from
        # your project on cloud console.
        # TODO(gbin): make that more user friendly.

        try:
            servacc_file = self.bot_config.GOOGLE_SERVICE_ACCOUNT
        except AttributeError:
            servacc_file = os.path.join(self.outdir, 'servacc.json')

        self.credentials = GoogleCredentials.from_stream(servacc_file)
        self.storage = build('storage', 'v1', credentials=self.credentials)

    @botcmd(split_args_with=' ')
    def project_set(self, mess, args):
        """Set the default project to work on.
        """
        if len(args) != 1 or args[0].strip() == '':
            yield "The syntax is !project set [name]"
            return
        self['project'] = args[0]
        if 'collect' not in self:
            yield "To improve Google Cloud ChatOps, we would like to collect anonymous & aggregated usage. " \
                  "If you agree with that please execute the command: '!collect agree'. At any moment you can disable" \
                  " it by executing the command '!collect disagree`."
        yield "Project %s set." % args[0]

    @botcmd
    def project(self, msg, _):
        """Gives the current project.
        """
        if 'project' in self:
            return "The project is set at %s." % self['project']
        return "No project has been set."

    @botcmd(split_args_with=' ')
    def bucket_set(self, mess, args):
        """Set the default bucket to work on.
        """
        if len(args) != 1 or args[0].strip() == '':
            return "The syntax is !bucket set [name]"
        self['bucket'] = args[0]
        return "Bucket %s set." % args[0]

    @botcmd
    def bucket(self, msg, _):
        """Gives the current bucket
        """
        if 'bucket' in self:
            return "The bucket is set at %s." % self['bucket']
        return "No bucket has been set."

    @botcmd
    def collect_agree(self, msg, _):
        self['collect'] = True
        return 'You rock ! Thanks for helping us improve Google Cloud ChatOps !'

    @botcmd
    def collect_disagree(self, msg, _):
        self['collect'] = False
        return 'Collection of any usage statistics has been explicitely disabled.'

    @cmdfilter
    def ga_filter(self, msg, cmd, args, dry_run):
        """
        :param msg: The original chat message.
        :param cmd: The command name itself.
        :param args: Arguments passed to the command.
        :param dry_run: True when this is a dry-run.
           Dry-runs are performed by certain commands (such as !help)
           to check whether a user is allowed to perform that command
           if they were to issue it. If dry_run is True then the plugin
           shouldn't actually do anything beyond returning whether the
           command is authorized or not.
        """
        logging.getLogger('requests.packages.urllib3').setLevel(logging.DEBUG)
        try:
            if 'collect' in self and self['collect']:
                if 'ga-cid' not in self:
                    self['ga-cid'] = str(uuid.uuid4())
                session = requests.Session()
                session.headers['User-Agent'] = 'Errbot/%s' % version.VERSION
                tracker = Tracker('UA-82261413-1',
                                  client_id=self['ga-cid'],
                                  requests_session=session)
                event = Event(category='commands',
                              action=cmd,
                              label=self._bot.all_commands[cmd].__self__.namespace,
                              value=1)
                self._bot.thread_pool.putRequest(WorkRequest(tracker.send, [event, ]))
        except:
            self.log.exception('Command tracking failed.')
        return msg, cmd, args
