#!/usr/bin/env python3
#
# Needs:
#
# pip install skyfield
# pip install arrow
# pip install pytz
# pip install ics
#

import os
import pytz
import arrow
import datetime

from skyfield import api
from skyfield import almanac
from ics import Calendar, Event

################################################################

# Arguments

# This is a standard filename for planetary positions.  You probably
# don't want to change this filename.
filename  = 'de421.bsp'

# Obtained from Google Maps (roughly the center of downtown
# Louisville)
longitude = 38.258865
latitude  = -85751557

# My local timezone name.
local_tz_name = 'America/Louisville'
local_tz      = pytz.timezone(local_tz_name)

# Semi-arbitrarily select a year's worth of dates
start_date = datetime.datetime(year=2018, month=12, day=23,
                               tzinfo=local_tz)
stop_date  = datetime.datetime(year=2019, month=12, day=31,
                               tzinfo=local_tz)

# The times I want lights to turn on
on_time    = datetime.time(hour=6, minute=30)

################################################################

# Download / load the JPL file

if os.path.exists(filename):
    print("Loading already-downloaded {f} file from JPL..."
          .format(f=filename))
    planets = api.load_file(filename)
else:
    print("Downloading planets file {f} from JPL..."
          .format(f=filename))
    planets = api.load(filename)

################################################################

# See https://github.com/skyfielders/python-skyfield/issues/218
# "maia.usno.navy.mil" is not resolving in DNS for me.  I used the
# "download the cached file from Google" trick to manually download
# deltat.data and deltat.preds and put them in the same folder where
# this file lives, and then skyfield just loads those local files.
print("Loading timescale...")
ts = api.load.timescale()

#--------------------------------

print("Seting up constants...")
one_day = datetime.timedelta(days=1)

here = api.Topos('{l} N'.format(l=longitude),
                 '{l} W'.format(l=latitude))

calendar   = Calendar()
delta_15m  = datetime.timedelta(minutes=15)
num_events = 0

#--------------------------------

print("Looping over dates...")
d = start_date
while d <= stop_date:
    t1 = ts.utc(d)
    t2 = ts.utc(d + one_day)
    times, _ = almanac.find_discrete(t1, t2,
                                     almanac.sunrise_sunset(planets, here))

    sunrise = times[0].astimezone(local_tz)
    sunset  = times[1].astimezone(local_tz)
    #print("Sunrise: {sunrise}, sunset: {sunset}"
    #      .format(sunrise=sunrise, sunset=sunset))

    # The precision of IFTTT isn't that great (deliver events +/- 5 to
    # 10 minutes.  So only bother to do something if sunrise is at
    # least 15 minutes after our desired on time.

    # Make sure to use the same timezone as the computed sunrise time
    start = datetime.datetime(year=d.year,
                              month=d.month,
                              day=d.day,
                              hour=on_time.hour,
                              minute=on_time.minute,
                              tzinfo=sunrise.tzinfo)

    if sunrise - start > delta_15m:
        event = Event()
        event.name = "Morning landscaping lights"
        event.begin = arrow.get(start)
        event.end = arrow.get(sunrise)
        calendar.events.add(event)
        num_events += 1
        print("Event: {start} - {end}"
              .format(start=start, end=sunrise))

    d += one_day

#--------------------------------

if num_events > 0:
    filename = 'events.ics'
    if os.path.exists(filename):
        os.unlink(filename)
    with open(filename, 'w') as my_file:
        my_file.writelines(calendar)
    print("Wrote {num} events to {f}"
          .format(num=num_events, f=filename))
