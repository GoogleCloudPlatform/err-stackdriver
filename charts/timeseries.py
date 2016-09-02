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

"""Pulls data from the Cloud Monitoring Timeseries API."""

from datetime import timedelta, datetime
import enum
import json

from apiclient import discovery
from oauth2client.client import GoogleCredentials


def _format_frequency(time_delta):
    return '{}s'.format(time_delta.total_seconds())


def _alignment_period_string_to_delta(string):
    """Turns an alignment period string into a timedelta.

    Args:
      string: (str) The alignment period string. Described in:
        cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.timeSeries/list
        Described as: "A duration in seconds with up to nine fractional digits,
        terminated by 's'." Example: "5s" meaning "5 seconds".
    """
    num_seconds = float(string[:-1])
    return timedelta(seconds=num_seconds)


class AlignmentPeriods(enum.Enum):
    """The alignment period for per-time series alignment.
    If present, alignmentPeriod must be at least 60 seconds.
    After per-time series alignment, each time series will contain data points
    only on the period boundaries.
    """
    # Note that MINUTES_1 is the minimum allowed alignment period.
    MINUTES_1 = _format_frequency(timedelta(minutes=1))
    MINUTES_5 = _format_frequency(timedelta(minutes=5))
    MINUTES_10 = _format_frequency(timedelta(minutes=10))
    MINUTES_15 = _format_frequency(timedelta(minutes=15))
    MINUTES_20 = _format_frequency(timedelta(minutes=20))
    MINUTES_30 = _format_frequency(timedelta(minutes=30))
    HOURS_1 = _format_frequency(timedelta(hours=1))
    HOURS_2 = _format_frequency(timedelta(hours=2))
    HOURS_3 = _format_frequency(timedelta(hours=3))
    HOURS_4 = _format_frequency(timedelta(hours=4))
    HOURS_6 = _format_frequency(timedelta(hours=6))
    HOURS_12 = _format_frequency(timedelta(hours=12))
    HOURS_24 = _format_frequency(timedelta(hours=24))


class PerSeriesAligners(enum.Enum):
    """Brings the data points in a single time series into temporal alignment.
    See: cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.timeSeries/list#Aligner
    """
    NONE = 'ALIGN_NONE'
    DELTA = 'ALIGN_DELTA'
    RATE = 'ALIGN_RATE'
    INTERPOLATE = 'ALIGN_INTERPOLATE'
    NEXT_OLDER = 'ALIGN_NEXT_OLDER'
    MIN = 'ALIGN_MIN'
    MAX = 'ALIGN_MAX'
    MEAN = 'ALIGN_MEAN'
    COUNT = 'ALIGN_COUNT'
    SUM = 'ALIGN_SUM'
    STDDEV = 'ALIGN_STDDEV'
    COUNT_TRUE = 'ALIGN_COUNT_TRUE'
    FRACTION_TRUE = 'ALIGN_FRACTION_TRUE'


class Client(object):
    def __init__(self, monitoring_api_client):
        self._monitoring_api_client = monitoring_api_client

    def list_timeseries(self,
                        project_id: str,
                        metric: str,
                        start_time: datetime,
                        end_time: datetime,
                        alignment_period: str=AlignmentPeriods.MINUTES_1.value,
                        per_series_aligner: str=PerSeriesAligners.MAX.value):
        """Lists time series.

        Args:
          project_id: E.g., "walkshare-monitor".
          metric: E.g., "compute.googleapis.com/instance/cpu/usage_time".
            See https://cloud.google.com/monitoring/api/metrics for more.
          start_time: A timezone-naive datetime object.
            Represents the datetime, in UTC, of the first moment to look at.
            The "moment" may include a summary of what happened from the N-1th
            moment, up until and including the given "start_time".  E.g., if start_time
            is 17:15, we will show a number for the x-value 17:15 that says either
            "this is what is happening at exactly 17:15", or "this is what happened
            between (17:14 and 17:15].  The former only applies when per_series_aligner
            is either None or "ALIGN_NONE".
            In any case, if you want to know what the world was looking like
            starting at 17:15, you should supply 17:15.
          end_time: A timezone-naive datetime object.
            Represents the datetime, in UTC, of the final moment to look at.
            The "moment" may include a summary of what happened from the N-1th
            moment, up until and including the given "end_time".  E.g., if end_time
            is 19:25, we will show a number for the x-value 19:25 that says either
            "this is what is happening at exactly 19:25", or "this is what happened
            between (19:24 and 19:25].  The former only applies when per_series_aligner
            is either None or "ALIGN_NONE".
            In any case, if you want to know what the world was looking like
            ending at 18:35, you should supply 18:35.
          alignment_period: The size of each timeseries data point bucket.
            I.e., if you supply '5s', each bucket contains 5 seconds of data,
            rounded off to the nearest 5 second window.
            If perSeriesAligner is None or equals ALIGN_NONE,
            then this field is ignored.
            If perSeriesAligner is specified and does not equal ALIGN_NONE,
            then this field must be defined.
            Defaults to minutely.
          per_series_aligner: The per-series aligner to use.
            Defaults to "ALIGN_MAX".

        Returns:
          timeSeries API response as documented here:
            cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.timeSeries/list
        """
        out = []

        each_value_represents_a_time_bucket = (
            per_series_aligner and
            per_series_aligner != PerSeriesAligners.NONE.value
        )
        if each_value_represents_a_time_bucket:
            bucket_delta = _alignment_period_string_to_delta(alignment_period)
            start_time -= bucket_delta

        default_request_kwargs = dict(
            name='projects/{}'.format(project_id),
            filter='metric.type="{}"'.format(metric),
            pageSize=10000,
            interval_startTime=_RFC3339(start_time),
            interval_endTime=_RFC3339(end_time)
        )
        if alignment_period:
            default_request_kwargs['aggregation_alignmentPeriod'] = alignment_period
        if per_series_aligner:
            default_request_kwargs['aggregation_perSeriesAligner'] = per_series_aligner

        def _do_request(next_page_token=None):
            kwargs = default_request_kwargs.copy()
            if next_page_token:
                kwargs['pageToken'] = next_page_token
            req = self._monitoring_api_client.projects().timeSeries().list(**kwargs)
            return req.execute()

        response = _do_request()
        out.extend(response.get('timeSeries', []))

        next_token = response.get('nextPageToken')
        while next_token:
            response = _do_request(next_token)
            out.extend(response.get('timeSeries', []))
            next_token = response.get('nextPageToken')

        return out


def _RFC3339(my_datetime):
    return my_datetime.isoformat("T") + "Z"


def new_client(credentials=None):
    if not credentials:
        credentials = GoogleCredentials.get_application_default()
    monitoring = discovery.build('monitoring', 'v3', credentials=credentials)
    return Client(monitoring)


if __name__ == '__main__':
    client = new_client()
    res = client.list_timeseries(
        project_id='walkshare-monitor',
        metric='appengine.googleapis.com/system/memory/usage',
        # 'compute.googleapis.com/instance/cpu/usage_time', # "compute.googleapis.com/instance/disk/read_bytes_count",
        start_time=datetime.utcnow() - timedelta(hours=2),
        end_time=datetime.utcnow(),
        per_series_aligner=PerSeriesAligners.MAX.value,
        alignment_period=AlignmentPeriods.MINUTES_1.value,
    )
    print(json.dumps(res))
