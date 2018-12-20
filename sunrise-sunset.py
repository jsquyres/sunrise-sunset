#!/usr/bin/env python
#
# Needs:
#
# pip install skyfield
# pip install pytz
#

import os
import pytz
import datetime

from skyfield import api
from skyfield import almanac

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
local_tz = pytz.timezone(local_tz_name)

# Semi-arbitrarily select a year's worth of dates
start_date = datetime.datetime(year=2018, month=12, day=20,
                               tzinfo=local_tz)
stop_date  = start_date + datetime.timedelta(weeks=52)

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

print("Seting up constants...")
one_day = datetime.timedelta(days=1)

here = api.Topos('{l} N'.format(l=longitude),
                 '{l} W'.format(l=latitude))

print("Looping over dates...")
d = start_date
while d <= stop_date:
    t1 = ts.utc(d)
    t2 = ts.utc(d + one_day)
    times, _ = almanac.find_discrete(t1, t2,
                                     almanac.sunrise_sunset(planets, here))

    sunrise = times[0].astimezone(local_tz)
    sunset  = times[1].astimezone(local_tz)
    print("Sunrise: {sunrise}, sunset: {sunset}"
          .format(sunrise=sunrise, sunset=sunset))

    d += one_day
