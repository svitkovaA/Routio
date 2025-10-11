from copy import deepcopy
from datetime import datetime
from gql import Client
from models.route_data import LegPreferences, RouteData
from services.route import route
from utils.planner_utils import create_waypoint_groups, filter_sort_trip_patterns
from utils.legs_processing import justify_time, process_legs
from services.otp_service import walk_bicycle_route
from config import OTP_URL
from models.bike_station_data import BikeStationData
from fastapi import APIRouter
from gql.transport.aiohttp import AIOHTTPTransport
import time as t

router = APIRouter()

@router.post("/changeBikeStation")
async def change_bike_station(data: BikeStationData):
    print("endpoint: change_bike_station")
    route_data = data.route_data
    compressed_legs = data.legs[:data.leg_index + 2] if route_data.arrive_by else data.legs[data.leg_index - 1:]
    time_to_depart = compressed_legs[-1]["aimedEndTime"] if route_data.arrive_by else compressed_legs[0]["aimedStartTime"]
    legs = data.original_legs
    new_pattern = {"legs": []}
    new_legs = []
    transport = AIOHTTPTransport(url=OTP_URL)
    async with Client(transport=transport) as session:
        if route_data.arrive_by:
            if data.origin_bike_station:
                i = 0
                compressed_index = 0
                waypoint_count = 1
                mode = ""
                while i < len(legs) - 1 and compressed_index < len(compressed_legs) - 1:
                    if legs[i]["mode"] == compressed_legs[compressed_index]["mode"]:
                        compressed_index += 1
                    if mode == legs[i]["mode"] and mode in ["bicycle", "foot"]:
                        waypoint_count += 1
                    mode = legs[i]["mode"]
                    i += 1
                base_legs = deepcopy(legs[i+1:])
                i = len(legs) - len(base_legs) - 1
                bike_pattern = await walk_bicycle_route(f"{data.bike_stations[data.new_index]["place"]["latitude"]}, {data.bike_stations[data.new_index]["place"]["longitude"]}", f"{legs[i]["toPlace"]["latitude"]}, {legs[i]["toPlace"]["longitude"]}", time_to_depart, "bicycle", session)
                new_legs.extend(bike_pattern[0]["legs"])
                new_legs.insert(0, {
                    "mode": "wait",
                    "color": "black",
                    "distance": 0,
                    "duration": route_data.bikesharing_lock_time * 60,
                    "pointsOnLink": {
                        "points": []
                    },
                    "bikeStationInfo": {
                        "rack": False,
                        "latitude": data.bike_stations[data.new_index]["place"]["latitude"],
                        "longitude": data.bike_stations[data.new_index]["place"]["longitude"],
                        "origin": True,
                        "selectedBikeStationIndex": data.new_index,
                        "bikeStations": data.bike_stations
                    }
                })
                leg_index = i - 2
                walk_pattern = await walk_bicycle_route(f"{legs[leg_index]["fromPlace"]["latitude"]}, {legs[leg_index]["fromPlace"]["longitude"]}", f"{data.bike_stations[data.new_index]["place"]["latitude"]} ,{data.bike_stations[data.new_index]["place"]["longitude"]}", time_to_depart, "foot", session)
                new_legs[:0] = walk_pattern[0]["legs"]
                justify_time({"legs": new_legs, "aimedEndTime": ""}, time_to_depart, True)
                waypoint_group = route_data.waypoints[:waypoint_count]
                waypoint_groups, _ = create_waypoint_groups(waypoint_group, [LegPreferences(mode=mode, exact=True) for mode in data.modes[:waypoint_count-1]])
                route_pattern = await route(waypoint_groups, new_legs[0]["aimedStartTime"], session, True, route_data, True)
                new_pattern["modes"] = data.modes[waypoint_count-1:]
                if len(route_pattern) > 0:
                    new_legs[:0] = route_pattern[0]["legs"]
                    new_pattern["modes"][:0] = route_pattern[0].get("modes", [])
                new_pattern["legs"] = new_legs + base_legs
                new_pattern["aimedEndTime"] = new_pattern["legs"][-1]["aimedEndTime"]
                process_legs(new_pattern)
            else:
                i = 0
                compressed_index = 0
                waypoint_count = 1
                mode = ""
                while i < len(legs) - 1 and compressed_index < len(compressed_legs) - 1:
                    if legs[i]["mode"] == compressed_legs[compressed_index]["mode"]:
                        compressed_index += 1
                    if mode == legs[i]["mode"] and mode in ["bicycle", "foot"]:
                        waypoint_count += 1
                    mode = legs[i]["mode"]
                    i += 1
                base_legs = deepcopy(legs[i+1:])
                i = len(legs) - len(base_legs) - 1
                walk_pattern = await walk_bicycle_route(f"{data.bike_stations[data.new_index]["place"]["latitude"]} ,{data.bike_stations[data.new_index]["place"]["longitude"]}", f"{legs[i]["toPlace"]["latitude"]}, {legs[i]["toPlace"]["longitude"]}", time_to_depart, "foot", session)
                new_legs.extend(walk_pattern[0]["legs"])
                new_legs.insert(0, {
                    "mode": "wait",
                    "color": "black",
                    "distance": 0,
                    "duration": route_data.bikesharing_lock_time * 60,
                    "pointsOnLink": {
                        "points": []
                    },
                    "bikeStationInfo": {
                        "rack": False,
                        "latitude": data.bike_stations[data.new_index]["place"]["latitude"],
                        "longitude": data.bike_stations[data.new_index]["place"]["longitude"],
                        "origin": False,
                        "selectedBikeStationIndex": data.new_index,
                        "bikeStations": data.bike_stations
                    }
                })
                leg_index = i - 2
                bike_pattern = await walk_bicycle_route(f"{legs[leg_index]["fromPlace"]["latitude"]}, {legs[leg_index]["fromPlace"]["longitude"]}", f"{new_legs[0]["bikeStationInfo"]["latitude"]}, {new_legs[0]["bikeStationInfo"]["longitude"]}", time_to_depart, "bicycle", session)
                new_legs[:0] = bike_pattern[0]["legs"]
                leg_index -= 1
                while leg_index > 0 and legs[leg_index]["mode"] != "foot":
                    if legs[leg_index]["mode"] == "bicycle":
                        waypoint_count -= 1
                    new_legs.insert(0, deepcopy(legs[leg_index]))
                    leg_index -= 1
                new_legs.insert(0, deepcopy(legs[leg_index]))
                justify_time({"legs": new_legs, "aimedEndTime": ""}, time_to_depart, True)
                waypoint_group = route_data.waypoints[:waypoint_count]
                waypoint_groups, _ = create_waypoint_groups(waypoint_group, [LegPreferences(mode=mode, exact=True) for mode in data.modes[:waypoint_count-1]])
                route_pattern = await route(waypoint_groups, new_legs[0]["aimedStartTime"], session, True, route_data, True)
                new_pattern["modes"] = data.modes[waypoint_count-1:]
                if len(route_pattern) > 0:
                    new_legs[:0] = route_pattern[0]["legs"]
                    new_pattern["modes"][:0] = route_pattern[0].get("modes", [])
                new_pattern["aimedEndTime"] = base_legs[-1]["aimedEndTime"] if len(base_legs) > 0 else new_legs[-1]["aimedEndTime"]
                new_pattern["legs"] = new_legs + base_legs
                process_legs(new_pattern)
        else:
            if data.origin_bike_station:
                i = len(legs) - 1
                compressed_index = len(compressed_legs) - 1
                waypoint_count = 1
                mode = ""
                while i >= 0 and compressed_index >= 0:
                    if legs[i]["mode"] == compressed_legs[compressed_index]["mode"]:
                        compressed_index -= 1
                    if mode == legs[i]["mode"] and mode in ["bicycle", "foot"]:
                        waypoint_count += 1
                    mode = legs[i]["mode"]
                    i -= 1

                base_legs = deepcopy(legs[:i+1])
                i = len(base_legs)
                walk_pattern = await walk_bicycle_route(f"{legs[i]["fromPlace"]["latitude"]}, {legs[i]["fromPlace"]["longitude"]}", f"{data.bike_stations[data.new_index]["place"]["latitude"]} ,{data.bike_stations[data.new_index]["place"]["longitude"]}", time_to_depart, "foot", session)
                new_legs.extend(walk_pattern[0]["legs"])
                new_legs.append({
                    "mode": "wait",
                    "color": "black",
                    "distance": 0,
                    "duration": route_data.bikesharing_lock_time * 60,
                    "pointsOnLink": {
                        "points": []
                    },
                    "bikeStationInfo": {
                        "rack": False,
                        "latitude": data.bike_stations[data.new_index]["place"]["latitude"],
                        "longitude": data.bike_stations[data.new_index]["place"]["longitude"],
                        "origin": True,
                        "selectedBikeStationIndex": data.new_index,
                        "bikeStations": data.bike_stations
                    }
                })
                leg_index = i + 2
                bike_pattern = await walk_bicycle_route(f"{new_legs[-1]["bikeStationInfo"]["latitude"]}, {new_legs[-1]["bikeStationInfo"]["longitude"]}", f"{legs[leg_index]["toPlace"]["latitude"]}, {legs[leg_index]["toPlace"]["longitude"]}", time_to_depart, "bicycle", session)
                new_legs.extend(bike_pattern[0]["legs"])
                leg_index += 1
                while leg_index < len(legs) and legs[leg_index]["mode"] != "foot":
                    if legs[leg_index]["mode"] == "bicycle":
                        waypoint_count -= 1
                    new_legs.append(deepcopy(legs[leg_index]))
                    leg_index += 1
                new_legs.append(deepcopy(legs[leg_index]))
                justify_time({"legs": new_legs, "aimedEndTime": ""}, time_to_depart, False)
                waypoint_group = route_data.waypoints[-waypoint_count:]
                routing_modes = data.modes[-waypoint_count+1:] if waypoint_count > 1 else []
                waypoint_groups, _ = create_waypoint_groups(waypoint_group, [LegPreferences(mode=mode, exact=True) for mode in routing_modes])
                # waypoint_groups, _ = create_waypoint_groups(waypoint_group, [LegPreferences(mode=mode, exact=True) for mode in data.modes[-waypoint_count+1:]])
                route_pattern = await route(waypoint_groups, new_legs[-1]["aimedEndTime"], session, True, route_data, True)
                
                print(waypoint_count, data.modes[:-waypoint_count+1], data.modes, data.modes[-waypoint_count+1:])
                # new_pattern["modes"] = data.modes[:-waypoint_count+1]
                new_pattern["modes"] = data.modes[:len(data.modes) - len(routing_modes)]
                if len(route_pattern) > 0:
                    new_legs.extend(route_pattern[0]["legs"])
                    new_pattern["modes"] += route_pattern[0].get("modes", [])
                    new_pattern["aimedEndTime"] = route_pattern[0]["aimedEndTime"]
                new_pattern["legs"] = base_legs + new_legs
                process_legs(new_pattern)
            else:
                i = len(legs) - 1
                compressed_index = len(compressed_legs) - 1
                waypoint_count = 1
                mode = ""
                while i >= 0 and compressed_index >= 0:
                    if legs[i]["mode"] == compressed_legs[compressed_index]["mode"]:
                        compressed_index -= 1
                    if mode == legs[i]["mode"] and mode in ["bicycle", "foot"]:
                        waypoint_count += 1
                    mode = legs[i]["mode"]
                    i -= 1
                waypoint_group = route_data.waypoints[-waypoint_count:]

                base_legs = deepcopy(legs[:i+1])
                i = len(base_legs)
                bike_pattern = await walk_bicycle_route(f"{legs[i]["fromPlace"]["latitude"]}, {legs[i]["fromPlace"]["longitude"]}", f"{data.bike_stations[data.new_index]["place"]["latitude"]} ,{data.bike_stations[data.new_index]["place"]["longitude"]}", time_to_depart, "bicycle", session)
                new_legs.extend(bike_pattern[0]["legs"])
                new_legs.append({
                    "mode": "wait",
                    "color": "black",
                    "distance": 0,
                    "duration": route_data.bikesharing_lock_time * 60,
                    "pointsOnLink": {
                        "points": []
                    },
                    "bikeStationInfo": {
                        "rack": False,
                        "latitude": data.bike_stations[data.new_index]["place"]["latitude"],
                        "longitude": data.bike_stations[data.new_index]["place"]["longitude"],
                        "origin": False,
                        "selectedBikeStationIndex": data.new_index,
                        "bikeStations": data.bike_stations
                    }
                })
                leg_index = i + 2
                walk_pattern = await walk_bicycle_route(f"{new_legs[-1]["bikeStationInfo"]["latitude"]}, {new_legs[-1]["bikeStationInfo"]["longitude"]}", f"{legs[leg_index]["toPlace"]["latitude"]}, {legs[leg_index]["toPlace"]["longitude"]}", time_to_depart, "foot", session)
                new_legs.extend(walk_pattern[0]["legs"])
                justify_time({"legs": new_legs, "aimedEndTime": ""}, time_to_depart, False)
                routing_modes = data.modes[-waypoint_count+1:] if waypoint_count > 1 else []
                print(waypoint_group)
                # TODO ten dalsi usek zacina mozno uz od posledneho legu nie az dalsieho waypointu?
                waypoint_groups, _ = create_waypoint_groups(waypoint_group, [LegPreferences(mode=mode, exact=True) for mode in routing_modes])
                route_pattern = await route(waypoint_groups, new_legs[-1]["aimedEndTime"], session, True, route_data, True)
                new_pattern["legs"] = base_legs + new_legs
                new_modes = data.modes[:len(data.modes) - len(routing_modes)]
                new_pattern["modes"] = new_modes
                if len(route_pattern) > 0:
                    new_pattern["legs"].extend(route_pattern[0]["legs"])
                    new_pattern["modes"] += route_pattern[0].get("modes", [])
                    new_pattern["aimedEndTime"] = route_pattern[0]["aimedEndTime"]
                else:
                    new_pattern["aimedEndTime"] = new_legs[-1]["aimedEndTime"]
                process_legs(new_pattern)

    return new_pattern

@router.post("/route")
async def get_route(data: RouteData):
    print("endpoint: get_route")
    start = t.perf_counter()
    results = {
        "tripPatterns": [],
        "active": True
    }
    time_to_depart = datetime.combine(data.date, data.time).isoformat()
    multimodal = data.mode == "transit,bicycle,walk"
    
    waypoint_groups, bike_segment_found = create_waypoint_groups(data.waypoints, data.leg_preferences, multimodal, data.mode)
    
    transport = AIOHTTPTransport(url=OTP_URL)
    async with Client(transport=transport, execute_timeout=20) as session:
        results["tripPatterns"] = await route(waypoint_groups, time_to_depart, session, multimodal, data, bike_segment_found, True)
    
    for pattern in results["tripPatterns"]: 
        process_legs(pattern)

    results["tripPatterns"] = filter_sort_trip_patterns(results["tripPatterns"], data)
    
    end = t.perf_counter()
    print(f"Duration: {end - start:.4f} sec")

    return results
