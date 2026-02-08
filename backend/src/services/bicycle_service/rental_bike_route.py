import asyncio
from copy import deepcopy
from typing import Dict, List
from models.types import BikeStationNode, Leg, TripPattern
from services.otp_service import walk_bicycle_route
from utils.legs_processing import justify_time
from services.bicycle_service.bike_station_service import optimal_destination_bike_station_choice, optimal_origin_bike_station_choice
from gql.client import AsyncClientSession

async def rental_bike_route(
    waypoints: List[str], 
    time_to_depart: str, 
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
    print("function: rental_bike_route")
    numOfNodes = 1 if best_option_only else 2

    origin_lat, origin_lon = map(float, waypoints[0].split(','))
    destination_lat, destination_lon = map(float, waypoints[-1].split(','))

    first_lat, first_lon = map(float, waypoints[1].split(','))
    last_lat, last_lon = map(float, waypoints[-2].split(','))

    tasks = [
        optimal_origin_bike_station_choice((origin_lat, origin_lon), (first_lat, first_lon), maximum_distance, public_bicycle, use_semicircle, session),
        optimal_destination_bike_station_choice((last_lat, last_lon), (destination_lat, destination_lon), maximum_distance, bicycle_public, use_semicircle, session)
    ]
    results = await asyncio.gather(*tasks)
    sortedOriginNodes = results[0]
    sortedDestinationNodes = results[1]

    intermediate_tasks = [
        walk_bicycle_route(waypoints[i], waypoints[i + 1], time_to_depart, "bicycle", bike_speed, session)
        for i in range(1, len(waypoints) - 2)
    ]
    intermediate_results = await asyncio.gather(*intermediate_tasks)
    intermediateLegs = [leg for res in intermediate_results for leg in res[0]["legs"]]

    origin_to_first_map: Dict[str, List[TripPattern]] = {}
    if not public_bicycle:
        origin_to_first_tasks = {
            origNode["place"]["id"]: walk_bicycle_route(waypoints[0], f"{origNode['place']['latitude']},{origNode['place']['longitude']}", time_to_depart, "foot", walk_speed, session)
            for origNode in sortedOriginNodes[:numOfNodes]
        }
        origin_to_first_results = await asyncio.gather(*origin_to_first_tasks.values())
        origin_to_first_map = dict(zip(origin_to_first_tasks.keys(), origin_to_first_results))

    last_to_dest_map: Dict[str, List[TripPattern]] = {}
    if not bicycle_public:
        last_to_dest_tasks = {
            destNode["place"]["id"]: walk_bicycle_route(f"{destNode['place']['latitude']},{destNode['place']['longitude']}", waypoints[-1], time_to_depart, "foot", walk_speed, session)
            for destNode in sortedDestinationNodes[:numOfNodes]
        }
        last_to_dest_results = await asyncio.gather(*last_to_dest_tasks.values())
        last_to_dest_map = dict(zip(last_to_dest_tasks.keys(), last_to_dest_results))


    async def build_trip(origNode: BikeStationNode, orig_index: int, destNode: BikeStationNode, dest_index: int) -> TripPattern:
        wait_leg: Leg = {
            "mode": "wait",
            "color": "black",
            "distance": 0,
            "duration": bike_lock_time * 60,
            "aimedStartTime": "",
            "aimedEndTime": "",
            "pointsOnLink": {
                "points": []
            },
            "bikeStationInfo": {
                "rack": False,
                "latitude": 0,
                "longitude": 0,
                "origin": True,
                "selectedBikeStationIndex": -1,
                "bikeStations": []
            }
        }
        startingBikeStation = f"{origNode['place']['latitude']},{origNode['place']['longitude']}"
        endBikeStation = f"{destNode['place']['latitude']},{destNode['place']['longitude']}"

        if public_bicycle:
            tripPattern: TripPattern = {"legs": [], "aimedEndTime": ""}
        else:
            tripPattern: TripPattern = deepcopy(origin_to_first_map[origNode["place"]["id"]][0])
        

        if len(waypoints) > 2:
            res = await walk_bicycle_route(startingBikeStation, waypoints[1], time_to_depart, "bicycle", bike_speed, session)
        else:
            res = await walk_bicycle_route(startingBikeStation, endBikeStation, time_to_depart, "bicycle", bike_speed, session)
        origin_wait_leg = deepcopy(wait_leg)
        if "fromPlace" in res[0]["legs"][0]:
            origin_wait_leg["bikeStationInfo"]["latitude"] = res[0]["legs"][0]["fromPlace"]["latitude"]
            origin_wait_leg["bikeStationInfo"]["longitude"] = res[0]["legs"][0]["fromPlace"]["longitude"]
            origin_wait_leg["bikeStationInfo"]["selectedBikeStationIndex"] = orig_index
            origin_wait_leg["bikeStationInfo"]["bikeStations"] = sortedOriginNodes
            copy_leg = deepcopy(origin_wait_leg)
            tripPattern["legs"].append(copy_leg)

            tripPattern["legs"].extend(res[0]["legs"])
            tripPattern["legs"].extend(intermediateLegs)

            if len(waypoints) > 2:
                res = await walk_bicycle_route(waypoints[-2], endBikeStation, time_to_depart, "bicycle", bike_speed, session)
                tripPattern["legs"].extend(res[0]["legs"])

            if "toPlace" in res[0]["legs"][-1]:
                destination_wait_leg = deepcopy(wait_leg)
                destination_wait_leg["bikeStationInfo"]["latitude"] = res[0]["legs"][-1]["toPlace"]["latitude"]
                destination_wait_leg["bikeStationInfo"]["longitude"] = res[0]["legs"][-1]["toPlace"]["longitude"]
                destination_wait_leg["bikeStationInfo"]["origin"] = False
                destination_wait_leg["bikeStationInfo"]["selectedBikeStationIndex"] = dest_index
                destination_wait_leg["bikeStationInfo"]["bikeStations"] = sortedDestinationNodes
                tripPattern["legs"].append(deepcopy(destination_wait_leg))

                if not bicycle_public:
                    tripPattern["legs"].extend(last_to_dest_map[destNode["place"]["id"]][0]["legs"])

                justify_time(tripPattern, time_to_depart, arrive_by)
                tripPattern["aimedEndTime"] = tripPattern["legs"][-1]["aimedEndTime"]
                tripPattern["bikeSegmentFound"] = True
        return tripPattern

    tasks = [
        build_trip(origNode, origIndex, destNode, destIndex)
        for origIndex, origNode in enumerate(sortedOriginNodes[:numOfNodes])
        for destIndex, destNode in enumerate(sortedDestinationNodes[:numOfNodes])
    ]
    trip_patterns = await asyncio.gather(*tasks)

    return trip_patterns

# End of file rental_bike_route.py
