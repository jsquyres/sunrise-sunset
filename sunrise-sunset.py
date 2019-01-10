#!/usr/bin/env python3
#
# Simple-ish script to generate events.ics: a file containing a series
# of calendar events for when I want landscaping lights on in the
# morning and again on in the evening.
#
# Generally turn on at 6:30am in the morning and turn off at sunrise
# (except when sunrise is before 6:45am), and turn on again at sunset
# and turn off at 11:15pm.
#
# I didn't use argparse to pass in command line arguments -- just edit
# the script below to fill in the values that you want.
#
# Needs:
#
# pip install skyfield
# pip install arrow
# pip install pytz
# pip install ics
#
# pip yelled at me that I got the latest arrow (0.12.something) and it
# was incompatible with ics (it wanted some exact 0.4.somethin version
# of arrow).  But it still seemed to produce good enough ICS files
# that imported just fine into Google Calendar.
#
# NOTE: Don't try to import more than a year or two of ICS data to
# Google Calendar at a time.  I tried to import a 5-year ICS file and
# it complained / said it coulnd't import.  But then later some (most?
# all?) of them showed up on the Google calendar anyway.  I suspect
# that there was some kind of timeout in the UI and the import might
# have fully worked... but you might want to just stay away from those
# kind of large imports to avoid ambiguities / duplicate entries, just
# to be safe.

import os
import pytz
import arrow
import datetime

from skyfield import api, almanac
from ics import Calendar, Event

################################################################

# Arguments

# This is a standard filename for planetary positions.  You probably
# don't want to change this filename.
filename      = 'de421.bsp'

# Obtained from Google Maps (roughly the center of downtown
# Louisville)
longitude     = 38.251505
latitude      = 85.758796

# My local timezone name.
local_tz_name = 'America/Louisville'
local_tz      = pytz.timezone(local_tz_name)

# Semi-arbitrarily select a year's worth of dates
start_date    = datetime.datetime(year=2019, month=1, day=1,
                               tzinfo=local_tz)
stop_date     = datetime.datetime(year=2019, month=12, day=31,
                               tzinfo=local_tz)

# The times I want lights to turn on
am_on_time    = datetime.time(hour=6,  minute=30)
pm_off_time   = datetime.time(hour=23, minute=15)

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
here = api.Topos('{l} N'.format(l=longitude),
                 '{l} W'.format(l=latitude))

calendar        = Calendar()
one_day         = datetime.timedelta(days=1)
fifteen_minutes = datetime.timedelta(minutes=15)
num_events      = 0

#--------------------------------

print("Looping over dates...")
d    = start_date
func = almanac.sunrise_sunset(planets, here)
while d <= stop_date:
    t1 = ts.utc(d)
    t2 = ts.utc(d + one_day)
    times, _ = almanac.find_discrete(t1, t2, func)

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
                              hour=am_on_time.hour,
                              minute=am_on_time.minute,
                              tzinfo=sunrise.tzinfo)

    if sunrise - start >= fifteen_minutes:
        event       = Event()
        event.name  = "Morning landscaping lights"
        event.begin = arrow.get(start)
        event.end   = arrow.get(sunrise)
        calendar.events.add(event)
        num_events += 1
        print("AM on event: {start} - {end}"
              .format(start=start, end=sunrise))

    # Make sure to use the same timezone as the computed sunrise time
    stop = datetime.datetime(year=d.year,
                             month=d.month,
                             day=d.day,
                             hour=pm_off_time.hour,
                             minute=pm_off_time.minute,
                             tzinfo=sunrise.tzinfo)
    event       = Event()
    event.name  = "Evening landscaping lights"
    event.begin = arrow.get(sunset)
    event.end   = arrow.get(stop)
    calendar.events.add(event)
    num_events += 1
    print("PM off event: {start} - {end}"
          .format(start=sunset, end=stop))

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
