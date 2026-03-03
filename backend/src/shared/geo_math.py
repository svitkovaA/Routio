"""
file: geo_math.py

Provides helper functions for geographic calculations
"""

from math import radians, sin, cos, sqrt, atan2, acos, degrees
from typing import Tuple

class GeoMath:
    """
    Helper functions for calculating distances and positions between two
    locations on Earth.
    """
    # Earths radius in kilometers
    EARTH_RADIUS_KM: float = 6371.0

    @staticmethod
    def haversine_distance_km(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculates the great-circle distance between two coordinates
        on the Earth using Haversine formula.

        Args:
            lat1: Latitude of the first point in degrees
            lon1: Longitude of the first point in degrees
            lat2: Latitude of the second point in degrees
            lon2: Longitude of the second point in degrees

        Returns:
            Distance between the two coordinates in kilometers
        """
        # Convert coordinate differences to radians
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)

        # Apply the Haversine formula
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return GeoMath.EARTH_RADIUS_KM * c

    @staticmethod
    def interpolate_point(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        distance_from_start: float
    ) -> Tuple[float, float]:
        """
        Computes an interpolated point on the great-circle path between
        two coordinates using linear interpolation.

        Args:
            lat1: Latitude of the first point in degrees
            lon1: Longitude of the first point in degrees
            lat2: Latitude of the second point in degrees
            lon2: Longitude of the second point in degrees
            distance_from_start: The distance from the first point in kilometers

        Returns:
            Tuple (latitude, longitude) of the interpolated point in degrees
        """
        # Distance between to coordinates
        total_distance = GeoMath.haversine_distance_km(lat1, lon1, lat2, lon2)

        # Prevents zero division when points are identical
        if total_distance == 0:
            return lat1, lon1

        # Convert coordinates from degrees to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        # Determine interpolation fraction along the path
        fraction = distance_from_start / total_distance

        # Clamp interpolation factor to valid range (0,1)
        fraction = max(0.0, min(1.0, fraction))

        # Convert coordinates to 3D coordinates
        x1 = cos(lat1_rad) * cos(lon1_rad)
        y1 = cos(lat1_rad) * sin(lon1_rad)
        z1 = sin(lat1_rad)

        x2 = cos(lat2_rad) * cos(lon2_rad)
        y2 = cos(lat2_rad) * sin(lon2_rad)
        z2 = sin(lat2_rad)

        # Compute the angle between two points
        dot = x1 * x2 + y1 * y2 + z1 * z2
        dot = min(1.0, max(-1.0, dot))
        omega = acos(dot)

        # Compute interpolation coefficients using spherical linear interpolation
        sin_omega = sin(omega)
        if sin_omega == 0:
            return lat1, lon1

        A = sin((1 - fraction) * omega) / sin_omega
        B = sin(fraction * omega) / sin_omega

        # Interpolate Cartesian coordinates 
        x = A * x1 + B * x2
        y = A * y1 + B * y2
        z = A * z1 + B * z2

        # Convert back from Cartesian coordinates to latitude/longitude in degrees
        lat = degrees(atan2(z, sqrt(x * x + y * y)))
        lon = degrees(atan2(y, x))

        return lat, lon
    
# End of file geo_math.py
