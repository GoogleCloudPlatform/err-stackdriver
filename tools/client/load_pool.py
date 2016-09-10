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

import threading
import time

import requests


def load_pool(addr):
    i = 0
    while True:
        i += 1
        raddr = addr + '-' + str(i)
        print('Hitting %s...' % raddr)
        print('Response %s.' % requests.get(raddr).content)


if __name__ == '__main__':
    t1 = threading.Thread(target=load_pool, args=('http://146.148.51.155/busyt1',))
    t2 = threading.Thread(target=load_pool, args=('http://146.148.51.155/busyt2',))
    t1.start()
    t2.start()
    while True:
        time.sleep(1)
