"""
file: vehicle_realtime_request_data.py

Defines request model for vehicle realtime data.
"""

from datetime import datetime
from pydantic import BaseModel

class VehicleRealtimeRequestData(BaseModel):
    trip_id: int                    # Trip identifier
    start_time: datetime            # Vehicle journey start time

# End of file vehicle_realtime_request_data.py
