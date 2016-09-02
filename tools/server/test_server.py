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


import http.server
import socketserver
from time import time
from random import randint
PORT = 80

INCREMENT = 1.0


def load(nb_seconds):
    start_time = time()
    d = {}
    while time() - start_time < nb_seconds:
        d[randint(0, 10000)] = randint(0, 10000)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        if self.path == '/':
            self.wfile.write(b"OK")
            return
        load(INCREMENT)
        self.wfile.write(b"Hello World !")
        return

httpd = socketserver.TCPServer(("", PORT), MyHandler)

print("serving at port", PORT)
httpd.serve_forever()
