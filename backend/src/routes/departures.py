from fastapi import APIRouter
from utils.legs_processing import justify_time
from models.departure_data import DepartureData
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/otherDepartures")
async def other_departures(data: DepartureData):
    print("endpoint: other_departures")
    index = data.public_leg_index
    legs = data.trip_pattern["originalLegs"]
    without_public_transport = True
    for i in range(index - 1):
        if legs[i]["mode"] not in ["bicycle", "foot", "wait", "transfer"]:
            without_public_transport = False

    chosen_dep = legs[index]["otherOptions"]["departures"][data.selected_index]
    legs[index]["aimedStartTime"] = chosen_dep["departureTime"]
    legs[index]["otherOptions"]["currentIndex"] = data.selected_index
    legs[index]["serviceJourney"]["direction"] = chosen_dep["direction"]

    start_dt = datetime.fromisoformat(legs[index]["aimedStartTime"])
    legs[index]["aimedEndTime"] = (start_dt + timedelta(seconds=legs[index]["duration"])).isoformat()

    legs[index]["arrivalAfterDeparture"] = False
    if without_public_transport:
        justify_time({"legs": legs[:index], "aimedEndTime": ""}, legs[index]["aimedStartTime"], True)
    else:
        if legs[index - 1]["aimedEndTime"] > legs[index]["aimedStartTime"]:
            legs[index]["arrivalAfterDeparture"] = True
    index += 1

    while index < len(legs):
        prev_end_dt = datetime.fromisoformat(legs[index - 1]["aimedEndTime"])

        if legs[index]["mode"] in ["foot", "bicycle", "wait", "transfer"]:
            legs[index]["aimedStartTime"] = prev_end_dt.isoformat()
        else:
            deps = legs[index].get("otherOptions", {}).get("departures", [])

            picked_i = None
            for i, departure in enumerate(deps):
                dep_dt = datetime.fromisoformat(departure["departureTime"])
                if dep_dt >= prev_end_dt:
                    picked_i = i
                    legs[index]["aimedStartTime"] = departure["departureTime"]
                    legs[index]["otherOptions"]["currentIndex"] = i
                    legs[index]["serviceJourney"]["direction"] = departure["direction"]
                    break

            legs[index]["arrivalAfterDeparture"] = False
            legs[index]["nonContinuousDepartures"] = False
            if picked_i is None and deps:
                last = deps[-1]
                legs[index]["aimedStartTime"] = last["departureTime"]
                legs[index]["otherOptions"]["currentIndex"] = len(deps) - 1
                legs[index]["serviceJourney"]["direction"] = last["direction"]
                legs[index]["nonContinuousDepartures"] = True

        start_dt = datetime.fromisoformat(legs[index]["aimedStartTime"])
        legs[index]["aimedEndTime"] = (start_dt + timedelta(seconds=legs[index]["duration"])).isoformat()

        index += 1

    data.trip_pattern["aimedEndTime"] = legs[-1]["aimedEndTime"]
    return data.trip_pattern
