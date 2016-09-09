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

"""Gets lines from the timeseries API."""

from datetime import datetime
from typing import Sequence, Any


class Line(object):
    def __init__(self, label, xs: Sequence[Any], ys: Sequence[float]):
        """A labeled series of X and Y points."""
        if len(xs) != len(ys):
            raise ValueError('must have equal number of xs and ys', xs, ys, label)
        self.label = label
        self.xs = xs
        self.ys = ys

    def __str__(self):
        return '<Line label="{label}">\nX:{xs}\nY:{ys}\n</Line>'.format(
            label=self.label, xs=self.xs, ys=self.ys)

    __repr__ = __str__


class Collection(object):
    """
    This is a collection of timeseries lines.
    """
    def __init__(self, lines: Sequence[Line], title: str, start: datetime, end: datetime):
        self._lines = lines
        self.title = title
        self.start, self.end = start, end
        self.min = min(line.xs[0] for line in lines)
        self.max = max(line.xs[-1] for line in lines)

    def __iter__(self):
        return iter(self._lines)

    def __len__(self):
        return len(self._lines)

    def __str__(self):
        return '<Collection title="{title}" start="{start}" end="{end}">\n{lines}\n</Collection>'.format(
            title=self.title, start=self.start, end=self.end,
            lines='\n'.join(map(str, self._lines)))

    __repr__ = __str__


def _datetime_of_point(point):
    """Gets the "point in time" or end of the bucket that a point shows.

    All points either represent a single moment in time, or a bucket of time, aka
    a TimeInterval (cloud.google.com/monitoring/api/ref_v3/rest/v3/TimeInterval).
    In the case of the former, the endTime must be used to find the moment.
    In the latter case, the endTime represents the inclusive end of the bucket.
    So regardless of what a point represents, the endTime is most meaningful.
    """
    rfc_string = point['interval']['endTime']
    return datetime.strptime(rfc_string, '%Y-%m-%dT%H:%M:%S.%fZ')


def _value_of_point(point):
    """Extracts the actual numeric value of a point.

    Only supports int64 and double point values.
    Strings, booleans, distribution and money are not supported.
    See cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.metricDescriptors#ValueType
    """
    pval = point['value']

    int64_value = pval.get('int64Value')
    if int64_value is not None:
        return int(int64_value)

    double_value = pval.get('doubleValue')
    if double_value is not None:
        return float(double_value)

    raise ValueError('point must have int or double value', point)


def _get_series_label_gce(api_series):
    return api_series['metric']['labels']['instance_name']


def _get_series_label_gae(api_series):
    metric_labels = api_series['metric'].get('labels', {})
    resource_labels = api_series.get('resource', {}).get('labels', {})

    source = metric_labels.get('source')
    module_id = resource_labels.get('module_id')
    version_id = resource_labels.get('version_id')

    if module_id and version_id and source:
        return '{module_id} ({version_id}) - {source}'.format(module_id=module_id, version_id=version_id, source=source)
    elif module_id and version_id and not source:
        return '{module_id} ({version_id})'.format(module_id=module_id, version_id=version_id)
    elif module_id and not version_id and source:
        return '{module_id} - {source}'.format(module_id=module_id, source=source)
    elif not module_id and version_id and source:
        return '{version_id} - {source}'.format(version_id=version_id, source=source)
    else:
        raise ValueError('need new GAE label template', api_series)


def get_collection_from_metrics(api, project_id, metric, start, end, time_interval_display):
    """Gets a collection of lines for a given project and metric.

    Args:
      api: (Stackdriver Monitoring API client)
      project_id: (str|int) The project ID from Cloud Platform.
      metric: (str) The metric name. Taken from-
        https://cloud.google.com/monitoring/api/metrics.
      start: (datetime) A timezone-naive datetime object.
        Represents the datetime, in UTC, of the first moment to look at.
      end: (datetime) A timezone-naive datetime object.
        Represents the datetime, in UTC, of the final moment to look at.
      time_interval_display: (interval.TimeIntervalDisplay)
    """
    api_serieses = api.list_timeseries(
        project_id=project_id, metric=metric, start_time=start, end_time=end,
        per_series_aligner=time_interval_display.per_series_aligner,
        alignment_period=time_interval_display.alignment_period,
    )
    if not api_serieses:
        raise ValueError('no series found', project_id, metric, start, end)

    if metric.startswith('compute.'):
        get_label = _get_series_label_gce
    else:
        get_label = _get_series_label_gae

    lines = []
    for api_series in api_serieses:
        points = api_series['points']
        points.sort(key=_datetime_of_point)

        xs, ys = [], []
        for pt in points:
            dt = _datetime_of_point(pt)
            if dt < start or dt > end:
                continue
            xs.append(dt)
            ys.append(_value_of_point(pt))

        lines.append(Line(xs=xs, ys=ys, label=get_label(api_series)))

    return Collection(lines=lines, title=metric, start=start, end=end)
