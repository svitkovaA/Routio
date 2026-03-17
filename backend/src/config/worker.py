"""
file: worker.py

Defines scheduled refresh intervals for background update tasks.
"""

# Interval for reloading static GTFS data, executes weekly on Monday at 2.00
GTFS_INTERVAL = {
    "hour": 2,
    "minute": 0,
    "weekday": 0
}

# Interval for reloading static GBFS data, executes weekly on Monday at 2.15
GBFS_INTERVAL = {
    "hour": 2,
    "minute": 15,
    "weekday": 0
}

# Interval for refreshing Lissy, executes weekly on Monday at 4.00
LISSY_INTERVAL = {
    "hour": 4
}

# Interval for polling GTFS-RT vehicle positions
VEHICLE_POSITION_INTERVAL = 10.0

# End of file worker.py
