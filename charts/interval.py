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

"""Describes how a time interval is displayed in a chart."""

import datetime

import matplotlib.dates as mdates

from charts import timeseries

HOURS_FORMATTER = mdates.DateFormatter('%H:%M')
DAYS_FORMATTER = mdates.DateFormatter('%x')


class TimeIntervalDisplay(object):
    def __init__(self, tick_minutes, alignment_period=None,
                 per_series_aligner=None,
                 major_formatter=mdates.DateFormatter('%H:%M')):
        """Visual configuration for the time interval to display in a graph.

        Args:
          major_tick_minutes: (int) The number of minutes between each tick.
          alignment_period: (Optional str) E.g., "120s". The size of each point's
            bucket of data. If None is provided, each point in the graph will refer
            to a moment in time rather than a bucket of time. Min is 60s.
          per_series_aligner: (Optional str) E.g., "ALIGN_MAX".  The aligner to use
            for each series.
          major_formatter: (Optional matplotlib.Formatter) The formatter for each
            major tick mark's x-axis time label. Defaults to one that turns an X point
            into HH:MM e.g., "17:35".
        """
        self.tick_minutes = tick_minutes
        self.alignment_period = alignment_period
        self.per_series_aligner = per_series_aligner
        self.major_formatter = major_formatter

    def __str__(self):
        return '<TimeIntervalDisplay {} />'.format(self.__dict__)

    __repr__ = __str__


def guess(start, end):
    # TODO: major_formatter should display the date if the start and end cross
    # a UTC date boundary.
    if start >= end:
        raise ValueError('start must be < end', start, end)

    delta = end - start
    formatter = HOURS_FORMATTER

    if delta <= datetime.timedelta(minutes=15):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_1
        tick_minutes = 1
    elif delta <= datetime.timedelta(minutes=30):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_1
        tick_minutes = 5
    elif delta <= datetime.timedelta(hours=1, minutes=15):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_1
        tick_minutes = 10
    elif delta <= datetime.timedelta(hours=3, minutes=15):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_1
        tick_minutes = 15
    elif delta <= datetime.timedelta(hours=6, minutes=30):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_5
        tick_minutes = 30
    elif delta <= datetime.timedelta(hours=12, minutes=30):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_10
        tick_minutes = 60
    elif delta <= datetime.timedelta(hours=24, minutes=30):
        alignment_period = timeseries.AlignmentPeriods.MINUTES_20
        tick_minutes = 120
    elif delta <= datetime.timedelta(days=2):
        alignment_period = timeseries.AlignmentPeriods.HOURS_1
        tick_minutes = 240
    elif delta <= datetime.timedelta(days=4):
        alignment_period = timeseries.AlignmentPeriods.HOURS_2
        tick_minutes = 480
    elif delta <= datetime.timedelta(days=8):
        alignment_period = timeseries.AlignmentPeriods.HOURS_4
        tick_minutes = 960
        formatter = DAYS_FORMATTER
    elif delta <= datetime.timedelta(days=16):
        alignment_period = timeseries.AlignmentPeriods.HOURS_12
        tick_minutes = 24 * 60
        formatter = DAYS_FORMATTER
    elif delta <= datetime.timedelta(days=100):
        alignment_period = timeseries.AlignmentPeriods.HOURS_24
        tick_minutes = 5 * 24 * 60
        formatter = DAYS_FORMATTER
    else:
        raise ValueError('missing suggestion', delta, start, end)

    return TimeIntervalDisplay(
        alignment_period=alignment_period.value,
        per_series_aligner=timeseries.PerSeriesAligners.MAX.value,
        tick_minutes=tick_minutes,
        major_formatter=DAYS_FORMATTER
    )
