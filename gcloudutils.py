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

import datetime

ONE_MINUTE = datetime.timedelta(minutes=1)
FIVE_MINUTES = datetime.timedelta(minutes=5)


def round_time(dt: datetime.datetime, delta: datetime.timedelta = FIVE_MINUTES, round_up: bool = True):
    """Round a datetime object to a multiple of a timedelta.

    Args:
      dt: (datetime.datetime) The datetime to round.
      delta: (Optional datetime.timedelta) We round to a multiple of this.
        Defaults to 5 minutes.
      round_up: (Optional bool) Whether to round the result up. Defaults to True.

    Returns:
      (datetime.datetime)
    """
    round_to = delta.total_seconds()
    seconds = (dt - dt.min).seconds
    rounding = (seconds + round_to / 2) // round_to * round_to
    out = dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)

    if round_up:
        return out if out >= dt else out + delta
    return out if out <= dt else out - delta
