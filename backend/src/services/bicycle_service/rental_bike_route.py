"""
file: rental_bike_route.py

Implements routing using rental bicycles. It selects origin and destination
bicycle stations with the highest weighted score and computes bicycle segment
between them. The bicycle segment is conditionally enriched with the walking
segment to or from bicycle station.
"""

import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Dict, List
from gql.client import AsyncClientSession
from models.route import BikeStationInfo, BikeStationNode, Leg, PointOnLink, TripPattern
from services.otp_service import walk_bicycle_route
from services.bicycle_service.bike_station_service import optimal_destination_bike_station_choice, optimal_origin_bike_station_choice
from utils.legs_processing import justify_time

async def rental_bike_route(
    waypoints: List[str], 
    time_to_depart: datetime, 
    best_option_only: bool, 
    arrive_by: bool, 
    bike_lock_time: int,
    bike_speed: float,
    walk_speed: float,
    session: AsyncClientSession, 
    maximum_distance: int = 1000, 
    public_bicycle: bool = False, 
    bicycle_public: bool = False, 
    use_semicircle: bool = False
) -> List[TripPattern]:
    """
    Computes route using rental bike on the given route segment

    Args:
        waypoints: Ordered list of coordinates
        time_to_depart: Departure time in ISO format
        best_option_only: If True, only the best station combinations are evaluated
        arrive_by: If True, routing is computed in arrive mode
        bike_lock_time: Time in minutes required for locking or unlocking the bicycle
        bike_speed: Cycling speed
        walk_speed: Walking speed
        session: Asynchronous GraphQL client session
        maximum_distance: Maximum search radius for bike stations
        public_bicycle: True, if the segment is being routed within public_bicycle mode
        bicycle_public: True, if the segment is being routed within bicycle_public mode
        use_semicircle: If True, restricts candidate stations to forward travel direction

    Returns:
        List of complete TripPattern objects representing rental bicycle routes
    """
    print("function: rental_bike_route")
    
    # Determine how many station alternatives should be evaluated
    num_of_nodes = 1 if best_option_only else 2

    # Parse origin and destination coordinates
    origin_lat, origin_lon = map(float, waypoints[0].split(','))
    destination_lat, destination_lon = map(float, waypoints[-1].split(','))

    # Parse first and last intermediate waypoints
    first_lat, first_lon = map(float, waypoints[1].split(','))
    last_lat, last_lon = map(float, waypoints[-2].split(','))

    # Select optimal origin and destination stations
    tasks = [
        optimal_origin_bike_station_choice(
            (origin_lat, origin_lon), 
            (first_lat, first_lon), 
            maximum_distance, 
            public_bicycle, 
            use_semicircle, 
            session
        ),
        optimal_destination_bike_station_choice(
            (last_lat, last_lon), 
            (destination_lat, destination_lon),
            maximum_distance, 
            bicycle_public, 
            use_semicircle, 
            session
        )
    ]

    results = await asyncio.gather(*tasks)
    sorted_origin_nodes = results[0]
    sorted_destination_nodes = results[1]

    # Compute intermediate bicycle legs
    intermediate_tasks = [
        walk_bicycle_route(
            waypoints[i],
            waypoints[i + 1], 
            time_to_depart, 
            "bicycle", 
            bike_speed, 
            session
        )
        for i in range(1, len(waypoints) - 2)
    ]
    intermediate_results = await asyncio.gather(*intermediate_tasks)

    # Flatten intermediate legs
    intermediate_legs = [
        leg 
        for res in intermediate_results 
        for leg in res[0].legs
    ]

    # Optional walking to origin station
    origin_to_first_map: Dict[str, List[TripPattern]] = {}
    if not public_bicycle:
        origin_to_first_tasks = {
            orig_node.place.id: walk_bicycle_route(
                waypoints[0], 
                f"{orig_node.place.latitude},{orig_node.place.longitude}", 
                time_to_depart, 
                "foot", 
                walk_speed, 
                session
            )
            for orig_node in sorted_origin_nodes[:num_of_nodes]
        }
        origin_to_first_results = await asyncio.gather(*origin_to_first_tasks.values())
        origin_to_first_map = dict(zip(origin_to_first_tasks.keys(), origin_to_first_results))

    # Optional walking from destination station
    last_to_dest_map: Dict[str, List[TripPattern]] = {}
    if not bicycle_public:
        last_to_dest_tasks = {
            dest_node.place.id: walk_bicycle_route(
                f"{dest_node.place.latitude},{dest_node.place.longitude}", 
                waypoints[-1], 
                time_to_depart, 
                "foot", 
                walk_speed, 
                session
            )
            for dest_node in sorted_destination_nodes[:num_of_nodes]
        }
        last_to_dest_results = await asyncio.gather(*last_to_dest_tasks.values())
        last_to_dest_map = dict(zip(last_to_dest_tasks.keys(), last_to_dest_results))

    # Build full trip pattern for each station combination
    async def build_trip(
        orig_node: BikeStationNode,
        orig_index: int,
        dest_node: BikeStationNode,
        dest_index: int
    ) -> TripPattern:
        """
        Constructs a single trip pattern for a given origin/destination bike station pair

        Args:
            orig_node: Origin bike station
            orig_index: Index of selected origin bike station
            dest_node: Destination bike station
            dest_index: Index of selected destination bike station
        
        Returns:
            Bike trip pattern between stations
        """

        # Template for wait leg for unlock/lock bicycle
        wait_leg = Leg(
            mode="wait",
            color="black",
            distance=0,
            duration=bike_lock_time * 60,
            aimedStartTime=datetime.min,    # Dummy value
            aimedEndTime=datetime.min,      # Dummy value
            pointsOnLink=PointOnLink(
                points=[]
            ),
            bikeStationInfo=BikeStationInfo(
                rack=False,
                latitude=0,                 # Dummy value
                longitude=0,                # Dummy value
                origin=True,
                selectedBikeStationIndex=-1,
                bikeStations=[]
            )
        )
        
        starting_bike_station = f"{orig_node.place.latitude},{orig_node.place.longitude}"
        end_bike_station = f"{dest_node.place.latitude},{dest_node.place.longitude}"

        # Initialize trip pattern
        if public_bicycle:
            trip_pattern = TripPattern(
                legs=[],
                aimedEndTime=datetime.min   # Dummy value
            )
        else:
            # Start with walking leg to origin station
            trip_pattern: TripPattern = deepcopy(origin_to_first_map[orig_node.place.id][0])
        
        # Compute first cycling segment
        if len(waypoints) > 2:
            res = await walk_bicycle_route(
                starting_bike_station, 
                waypoints[1], 
                time_to_depart, 
                "bicycle", 
                bike_speed, 
                session
            )
        else:
            res = await walk_bicycle_route(
                starting_bike_station, 
                end_bike_station, 
                time_to_depart, 
                "bicycle", 
                bike_speed, 
                session
            )
       
        # Insert bike unlock time
        origin_wait_leg = deepcopy(wait_leg)
        if res[0].legs[0].fromPlace and origin_wait_leg.bikeStationInfo:
            origin_wait_leg.bikeStationInfo.latitude = res[0].legs[0].fromPlace.latitude
            origin_wait_leg.bikeStationInfo.longitude = res[0].legs[0].fromPlace.longitude
            origin_wait_leg.bikeStationInfo.selectedBikeStationIndex = orig_index
            origin_wait_leg.bikeStationInfo.bikeStations = sorted_origin_nodes
            
            copy_leg = deepcopy(origin_wait_leg)
            trip_pattern.legs.append(copy_leg)

            # Add cycling and intermediate legs
            trip_pattern.legs.extend(res[0].legs)
            trip_pattern.legs.extend(intermediate_legs)

            # Add final cycling segment if needed
            if len(waypoints) > 2:
                res = await walk_bicycle_route(
                    waypoints[-2], 
                    end_bike_station, 
                    time_to_depart, 
                    "bicycle", 
                    bike_speed, 
                    session
                )
                trip_pattern.legs.extend(res[0].legs)

            # Insert bike lock time 
            destination_wait_leg = deepcopy(wait_leg)
            if res[0].legs[-1].toPlace and destination_wait_leg.bikeStationInfo:
                destination_wait_leg.bikeStationInfo.latitude = res[0].legs[-1].toPlace.latitude
                destination_wait_leg.bikeStationInfo.longitude = res[0].legs[-1].toPlace.longitude
                destination_wait_leg.bikeStationInfo.origin = False
                destination_wait_leg.bikeStationInfo.selectedBikeStationIndex = dest_index
                destination_wait_leg.bikeStationInfo.bikeStations = sorted_destination_nodes
                trip_pattern.legs.append(deepcopy(destination_wait_leg))

                # Add final walking segment if needed
                if not bicycle_public:
                    trip_pattern.legs.extend(last_to_dest_map[dest_node.place.id][0].legs)

                # Adjust trip timing
                justify_time(trip_pattern, time_to_depart, arrive_by)

                trip_pattern.aimedEndTime = trip_pattern.legs[-1].aimedEndTime
                trip_pattern.bikeSegmentFound = True

        return trip_pattern

    # Evaluate all station combinations
    tasks = [
        build_trip(orig_node, orig_index, dest_node, dest_index)
        for orig_index, orig_node in enumerate(sorted_origin_nodes[:num_of_nodes])
        for dest_index, dest_node in enumerate(sorted_destination_nodes[:num_of_nodes])
    ]
    trip_patterns = await asyncio.gather(*tasks)

    return trip_patterns

# End of file rental_bike_route.py
