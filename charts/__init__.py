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

"""Generates a chart of Cloud Monitoring metrics. Not thread safe."""
# Be sure we put matplotlib on the right backend before importing other classes from it.
from numbers import Number
from typing import Sequence, List

from matplotlib import use

from charts.line import Collection

use('Agg')

import base64
import datetime
import io
import math

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

import gcloudutils
from charts.interval import TimeIntervalDisplay

_FONTDICT = {
    'family': 'sans-serif',
    'color': 'lightgrey',
    'weight': 'light',
    'size': 15,
}
_LEGEND_LABELS_PER_ROW = 2


def _format_percent(value: float, unused_point=None):
    return ('%3.1f' % (value * 100.0)) + '%'


def _format_number(value: float, unused_point=None, suffix=''):
    # This function produces some weird results when some points on the graph
    # are in one of the ranges (<1e3, 1e3, 1e6, 1e9, >1e9), and some points are
    # in another range.  E.g., you might have a y-axis that looks like
    # 500, 1.5k, 3.9M.
    # TODO: It might be better if all of the values get formatted
    # based on the largest bucket across all values.
    abs_value = abs(value)
    if abs_value < 1e3:
        value = str(value)
    elif abs_value < 1e6:
        value = '%3.1fk' % (value / 1e3)
    elif abs_value < 1e9:
        value = '%3.1fM' % (value / 1e6)
    else:
        value = '%3.1fB' % (value / 1e9)
    return value + suffix


def _compute_graph_dimensions(num_lines):
    width = 8
    height = 6
    num_legend_labels_in_7_inch_height = 6
    remaining = num_lines - num_legend_labels_in_7_inch_height
    if remaining <= 0:
        return width, height

    rows_remaining = math.ceil(remaining / _LEGEND_LABELS_PER_ROW)
    height += rows_remaining * 2

    return width, height


def _generate_subtitle(lines):
    nice = lambda t: t.strftime('%Y-%m-%d %H:%M:%S')
    return '[%s - %s UTC]' % (nice(lines.start), nice(lines.end))


def _get_x_ticks(lines, time_interval_display):
    tick_delta = datetime.timedelta(minutes=time_interval_display.tick_minutes)
    if tick_delta > gcloudutils.ONE_MINUTE:
        first_tick = gcloudutils.round_time(lines.min, gcloudutils.FIVE_MINUTES, round_up=True)
        final_tick = gcloudutils.round_time(lines.max, gcloudutils.FIVE_MINUTES, round_up=False)
    else:
        first_tick = gcloudutils.round_time(lines.min, gcloudutils.ONE_MINUTE, round_up=True)
        final_tick = gcloudutils.round_time(lines.max, gcloudutils.ONE_MINUTE, round_up=False)

    t = first_tick
    while t <= final_tick:
        yield t
        t += tick_delta


def generate_timeseries_linechart(collection: Collection, time_interval_display: TimeIntervalDisplay,
                                  y_formatter=_format_number, outfile=None):
    """Generates a chart.

    Args:
      collection: (line.Collection) The x-y lines to plot.
      time_interval_display: TimeIntervalDisplay.
      y_formatter: (Optional function) Function that must be called with 2 *args.
        the "value" and the "point" to format.  Must return a string that
        represents the given value & point.
        Defaults to the _FormatNumber function without a suffix.
        I'd recommend adding a "/h" or "/m" suffix to the formatted output if
        your time_interval_display involves a PerSeriesAligner of SUM/MEAN/COUNT.
      outfile: (Optional file-like object | str) If None, shows a matplotlib GUI.
        If str, the name of the file to save to.
        Should have a .png extension.  Otherwise, should be sys.stdout/StringIO().
    """
    fig, ax = plt.subplots()
    num_lines = len(collection)
    fig.set_size_inches(*_compute_graph_dimensions(num_lines))

    # Make the chart black-on-black.
    plt.style.use('dark_background')
    ax.set_axis_bgcolor('black')

    plt.locator_params(axis='y', nbins=6)
    color_iter = plt.cm.rainbow(np.linspace(0, 1, num_lines))
    for line, color in zip(collection, color_iter):
        actual_label = '{label}: {current_value}'.format(
            label=line.label, current_value=y_formatter(line.ys[-1]))
        ax.plot(line.xs, line.ys, label=actual_label, linewidth=1.8, color=color)

    plt.grid(b=True, which='major', color='lightgrey', linestyle='-')
    plt.grid(axis='x', which='minor', color='grey', linestyle='-')

    ax.yaxis.set_ticks_position('left')  # Only show left y ticks.
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(y_formatter))
    # Hide the first y label since we know it's 0.
    ax.yaxis.get_major_ticks()[0].label1.set_visible(False)

    plt.xticks(list(_get_x_ticks(collection, time_interval_display)), rotation=30)
    ax.xaxis.set_ticks_position('bottom')  # Only show bottom x ticks.
    ax.xaxis.set_major_formatter(time_interval_display.major_formatter)

    top_of_chart_ytick_loc = ax.yaxis.get_majorticklocs()[-1]
    ax.axhline(y=top_of_chart_ytick_loc, ls='-', color='lightgrey')
    bottom_of_chart_ytick_loc = ax.yaxis.get_majorticklocs()[0]
    ax.axhline(y=bottom_of_chart_ytick_loc, ls='-', color='lightgrey', linewidth=3)
    ax.tick_params(axis='x', which='major', labelcolor='lightgrey', labelsize=10)
    ax.tick_params(axis='y', which='major', labelcolor='lightgrey', labelsize=10)

    # plt.suptitle(_generate_subtitle(lines), x=0.24, y=0.945, fontdict=_FONTDICT)
    plt.title(collection.title, loc='left', y=1.08, x=-0.08, fontdict=_FONTDICT)

    # Shrink current axis's height by 10% on the bottom and put a legend in there.
    box = ax.get_position()
    ax.set_position(
        [box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
                       ncol=_LEGEND_LABELS_PER_ROW, frameon=False)
    for text in legend.get_texts():
        plt.setp(text, color='lightgrey', fontsize=12)

    if outfile:
        fig.savefig(outfile, format='png', dpi=120)
    else:
        plt.show()


def generate_barchart(title: str, ylabel: str, labels: List[str], values: List[Number], outfile=None):
    ind = np.arange(len(values))
    width = 1
    fig, ax = plt.subplots()
    ax.bar(ind, values, width, color='r')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(labels, rotation=45)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    if outfile:
        fig.savefig(outfile, format='png', dpi=120)
    else:
        plt.show()


def stringify(**kwargs):
    """Returns a base64-encoded chart for the given kwargs."""
    if 'outfile' in kwargs:
        raise ValueError('must not set chart outfile', kwargs)
    with io.BytesIO() as out:
        generate_timeseries_linechart(outfile=out, **kwargs)
        return base64.encodebytes(out.getvalue()).decode()
