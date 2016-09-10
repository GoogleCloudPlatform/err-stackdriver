#!/usr/bin/env python3

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

import time

import requests


def post_alert(addr):
    print('Posting an alert ...')

    incident = {'incident': {'started_at': int(time.time()),
                             'incident_id': 'f2e08c333dc64cb09f75eaab355393bz',
                             'resource_id': 'i-4a266a2d',
                             'state': 'open',
                             'condition_name': 'CPU usage',
                             'ended_at': None,
                             'url': 'https://app.stackdriver.com/incidents/f2e08c333dc64cb09f75eaab355393bz',
                             'resource_name': 'www1',
                             'policy_name': 'Webserver Health',
                             'summary': 'CPU (agent) for www1 is above the threshold of 90% with a value of 99%'
                             },
                'version': 1}
    r = requests.post(addr, json=incident)
    print('Done: Replied %s' % r.content)


if __name__ == '__main__':
    post_alert('http://localhost:3141/alert')
