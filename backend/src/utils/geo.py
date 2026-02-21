"""
file: geo.py

Helper functions for geographic computations, including:
- the distance calculation using the Haversine formula,
- interpolation between coordinates,
- merging spatially close and duplicate results,
- estimating the distance threshold at which cycling becomes 
  more time efficient than walking.
"""

from math import radians, sin, cos, sqrt, atan2, acos, degrees
from typing import List, Tuple
from models.suggestions import Suggestion

def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate great-circle distance between two points on the Earth
    using Haversine formula

    Args:
        lat1: Latitude of the first point
        lon1: Longitude of the first point
        lat2: Latitude of the second point
        lon2: Longitude of the second point

    Returns:
        Distance between the two points in kilometers
    """
    # Earths radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    # Convert coordinate differences to radians
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    # Apply the Haversine formula
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS_KM * c

def interpolate_point(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    distance_from_start: float
) -> Tuple[float, float]:
    """
    Computes an interpolated point on the great-circle path between two coordinates

    Args:
        lat1, lon1: Latitude and longitude of the first point
        lat2, lon2: Latitude and longitude of the second point
        distance_from_start: The distance from the first point in kilometers

    Returns:
        tuple (latitude, longitude) of the new point in the degrees
    """
    print("function: interpolate_point")
    # Distance between to coordinates
    total_distance = haversine_distance_km(lat1, lon1, lat2, lon2)

    # Prevents zero division
    if total_distance == 0:
        return lat1, lon1

    # Convert coordinates from degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    # Fraction of the total distance at which is need to interpolate
    f = distance_from_start / total_distance

    # Clamp
    f = max(0.0, min(1.0, f))

    # Convert points to 3D 
    x1 = cos(lat1_rad) * cos(lon1_rad)
    y1 = cos(lat1_rad) * sin(lon1_rad)
    z1 = sin(lat1_rad)

    x2 = cos(lat2_rad) * cos(lon2_rad)
    y2 = cos(lat2_rad) * sin(lon2_rad)
    z2 = sin(lat2_rad)

    # Compute the angle between two points on the sphere
    dot = x1 * x2 + y1 * y2 + z1 * z2
    dot = min(1.0, max(-1.0, dot))
    omega = acos(dot)

    # Compute interpolation coefficients using spherical linear interpolation
    sin_omega = sin(omega)
    A = sin((1 - f) * omega) / sin_omega
    B = sin(f * omega) / sin_omega

    # Interpolate Cartesian coordinates 
    x = A * x1 + B * x2
    y = A * y1 + B * y2
    z = A * z1 + B * z2

    # Convert from Cartesian to lat and lon in degrees
    lat = degrees(atan2(z, sqrt(x * x + y * y)))
    lon = degrees(atan2(y, x))

    # Return latitude and longitude of the new point in degrees
    return lat, lon

def merge_close_results(results: List[Suggestion], max_distance: float=20) -> List[Suggestion]:
    """
    Merge close and duplicate search results

    Args:
        results: List of search results containing location information
        max_distance: Maximal distance in meters for merging close results

    Returns:
        New list of merged results
    """
    print("function: merge_close_results")
    merged: List[Suggestion] = []
    
    for candidate in results:
        duplicate = False
        for existing in merged:
            same_name = (
                candidate["name"] == existing["name"] and
                candidate.get("type") == existing.get("type") and
                candidate.get("country") == existing.get("country") and
                candidate.get("city") == existing.get("city") and
                (
                    candidate.get("street") == existing.get("street") or
                    candidate.get("street") is None or
                    existing.get("street") is None
                )
            )

            too_close = (
                haversine_distance_km(
                    candidate["lat"],
                    candidate["lon"],
                    existing["lat"],
                    existing["lon"]
                ) * 1000 < max_distance
            )

            if same_name or too_close:
                duplicate = True
                break

        if not duplicate:
            merged.append(candidate)

    return merged

def get_borderline_distance(
    bike_average_speed: float,
    walk_average_speed: float,
    bike_lock_time: int,
    bike_walk_distance: float
) -> float:
    """
    Calculate distance at which cycling becomes more time-efficient than walking

    Args:
        bike_average_speed: Average cycling speed in km/h
        walk_average_speed: Average walking speed in km/h
        bike_lock_time: Required time to lock/unlock bike in minutes
        bike_walk_distance: Additional distance for walking to/from bike station in km
    
    Returns:
        The borderline distance when cycling equals to walking time in kilometers
    """
    print("function: get_borderline_distance")

    # Prevent computing when cycling speed is slower than walking speed
    if bike_average_speed <= walk_average_speed:
        return float("inf")
    
    bike_lock_time_hours = bike_lock_time / 60

    distance = bike_walk_distance + ((bike_lock_time_hours) / (1 / walk_average_speed - 1 / bike_average_speed))
    
    return distance

# End of file geo.py
