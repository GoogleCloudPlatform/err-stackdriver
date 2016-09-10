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
import os
from datetime import datetime, timedelta

from errbot import Message
from errbot import botcmd, BotPlugin
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import charts
import charts.line
import charts.timeseries
from charts import interval, line, timeseries


def get_ts():
    now = datetime.now()
    return '%s.%d' % (now.strftime('%Y%m%d-%H%M%S'), now.microsecond)


class GoogleCloudMonitoring(BotPlugin):
    """This is a binding example from errbot to Google Cloud"""

    def activate(self):
        super().activate()
        self.gc = self.get_plugin('GoogleCloud')
        self.credentials = self.gc.credentials
        if not self.credentials:
            self.log.error('FATAL: GCloud plugin could not load credentials.')
            return
        if 'bookmarks' not in self:
            self['bookmarks'] = []

        self.monitoring = build('monitoring', 'v3', credentials=self.credentials)

    def project(self):
        if 'project' not in self.gc:
            raise Exception('No Project set.')
        return self.gc['project']

    def bucket(self):
        if 'bucket' not in self.gc:
            raise Exception('No Bucket set.')
        return self.gc['bucket']

    def gen_graph(self, metric, prefix):
        filename = '%s-%s.%s.png' % (prefix.replace('/', '_'), self.project(), get_ts())
        output = os.path.join(self.gc.outdir, filename)
        end = datetime.utcnow() + timedelta(minutes=1)
        start = end - timedelta(minutes=15)

        tid = interval.guess(start, end)
        tid.per_series_aligner = None
        tid.alignment_period = None
        # These can be used with the default y_formatter:
        # compute.googleapis.com/firewall/dropped_packets_count
        # appengine.googleapis.com/system/cpu/usage
        # compute.googleapis.com/instance/cpu/utilization',
        # compute.googleapis.com/instance/disk/write_bytes_count
        # compute.googleapis.com/instance/network/received_bytes_count
        # compute.googleapis.com/instance/network/sent_packets_count
        # compute.googleapis.com/instance/network/received_bytes_count
        # Needs y_formatter=_FormatPercent
        # compute.googleapis.com/instance/cpu/utilization
        collection = line.get_collection_from_metrics(
            api=timeseries.Client(self.monitoring),
            project_id=self.project(),
            metric=metric,
            start=start, end=end, time_interval_display=tid)
        charts.generate_timeseries_linechart(
            collection=collection,
            time_interval_display=tid,
            outfile=output,
            # y_formatter=_FormatPercent,
        )
        with open(output, 'rb') as source:
            media = MediaIoBaseUpload(source, mimetype='image/png')
            response = self.gc.storage.objects().insert(bucket=self.bucket(),
                                                        name=filename,
                                                        media_body=media,
                                                        predefinedAcl='publicRead').execute()
        return response['mediaLink']

    @botcmd
    def metric_search(self, msg, args):
        """List the monitoring metrics for the current project.
        """
        out = []

        default_request_kwargs = dict(
            name='projects/{}'.format(self.project()),
        )
        if args:
            default_request_kwargs['filter'] = 'metric.type : "%s"' % args

        def _do_request(next_page_token=None):
            kwargs = default_request_kwargs.copy()
            if next_page_token:
                kwargs['pageToken'] = next_page_token
            req = self.monitoring.projects().metricDescriptors().list(**kwargs)
            return req.execute()

        response = _do_request()
        out.extend(response.get('metricDescriptors', []))

        next_token = response.get('nextPageToken')
        while next_token:
            response = _do_request(next_token)
            out.extend(response.get('metricDescriptors', []))
            next_token = response.get('nextPageToken')

        return '\n'.join('* **%s** %s' % (m['type'], m['description']) for m in out)

    @botcmd
    def metric_addbookmark(self, _, args: str):
        """
        Stores a metric bookmark and assigns it a number.
        """
        with self.mutable('bookmarks') as bookmarks:
            bookmarks.append(args)
        return "Your bookmark has been stored, you can chart it with !metrics chart %i." % (len(bookmarks) - 1)

    @botcmd
    def metric_bookmarks(self, _, args: str):
        """
        Stores a metric bookmark and assigns it a number.
        """
        return '\n'.join('%i: %s' % (i, bookmark) for i, bookmark in enumerate(self['bookmarks']))

    @botcmd
    def metric_delbookmark(self, _, args: str):
        """
        Removes a metric bookmark.
        """
        with self.mutable('bookmarks') as bookmarks:
            del bookmarks[int(args)]
        return "%i bookmarks have been defined." % len(bookmarks)

    @botcmd
    def metric_chart(self, msg: Message, args: str):
        """ Charts a metric or a bookmark of a metric.
        """
        try:
            metric_type = self['bookmarks'][int(args)]
        except ValueError:
            metric_type = args.strip()

        res = self.monitoring.projects().metricDescriptors().list(name='projects/%s' % self.project(),
                                                                  filter='metric.type = "%s"' % metric_type).execute()
        metrics = res.get('metricDescriptors', [])

        if not metrics:
            return 'Could not find metric %s' % args

        metric = metrics[0]

        url = self.gen_graph(metric['type'], metric['type'])
        now = datetime.now()
        now = datetime(day=now.day,
                       month=now.month,
                       year=now.year,
                       hour=now.hour,
                       minute=now.minute,
                       second=now.second)
        self.send_card(in_reply_to=msg,
                       title=metric['description'],
                       image=url,
                       fields=(('Project', self.project()),
                               ('Metric', metric),
                               ('From', str(now - timedelta(minutes=15))),
                               ('To', str(now)),
                               ))
