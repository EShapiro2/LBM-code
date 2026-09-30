# Full taxi trip records for the Manhattan experiment hour

Retrieved September 26, 2026 from NYC Open Data's **2015 Yellow Taxi Trip Data**, dataset `2yzn-sicd`.
Source: https://data.cityofnewyork.us/Transportation/2015-Yellow-Taxi-Trip-Data/2yzn-sicd

The JSON contains **26,011 rides** picked up January 15, 2015, from 08:00 inclusive to 09:00 exclusive, in the source's New York local wall-clock time. It includes all reported pickup locations citywide. Of these, **6,495** were picked up before 08:15.

Each record includes pickup_datetime, dropoff_datetime, pickup_longitude, pickup_latitude, dropoff_longitude and dropoff_latitude. Original fields such as fare and trip distance are retained. Values are strings as returned by the source API. Coordinates are geographic longitude/latitude, not the local kilometer coordinates of the disk simulation.

These records have NOT yet been matched to the 24,101 Manhattan pickups in the original compressed extract or the 5,986 points used in the disk experiment. They include pickups outside Manhattan and retain source data errors. All records have both timestamp and coordinate fields, but **546** have a zero in at least one endpoint coordinate, and **21** have a drop-off timestamp no later than pickup. These categories may overlap. Filter or flag such records before a ride-allocation simulation.

Pickup and drop-off timestamps describe meter engagement and disengagement. They are not passenger request times. Vendor ID identifies the technology provider, not an individual driver. This file does not provide an identified driver's trajectory or a live inventory of available cars.

`retrieve.py` reproduces the hour query using Python's standard library and checks the returned record count against a separate API count query. `source_url.txt` records the exact query used for this download. Original records are preserved without filtering or deduplication.
