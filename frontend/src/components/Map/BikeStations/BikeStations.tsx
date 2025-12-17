/**
 * @file BikeStations.tsx
 * @brief Displays bike stations on the map, allows changing origin and destination stations
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { CircleMarker, Popup, useMapEvent } from "react-leaflet";
import { API_BASE_URL } from "../../config/config";
import { useSettings } from "../../SettingsContext";
import { useInput } from "../../InputContext";
import { useResult } from "../../ResultContext";

function BikeStations() {
    const {
        waypoints,
        arriveBy,
        useOwnBike,
        preference,
    } = useInput();

    const {
        maxTransfers,
        selectedModes,
        maxBikeDistance,
        bikeAverageSpeed,
        maxBikesharingDistance,
        bikesharingAverageSpeed,
        maxWalkDistance,
        walkAverageSpeed,
        bikesharingLockTime,
        bikeLockTime
    } = useSettings();

    const {
        results, setResults,
        showResults,
        resultActiveIndex,
        selectedTripPatternIndex,
        pattern
    } = useResult();

    const changeBikeStation = async (originBikeStation: boolean, bikeStationIndex: number, bikeStations: any[], legIndex: number) => {
        const legs = pattern.legs;
        const originalLegs = pattern.originalLegs;
        const modes = pattern.modes;
        
        let waypointsArray: string[] = [];
        for (let i = 0; i < waypoints.length; i++) {
            waypointsArray.push(waypoints[i].lat + ', ' + waypoints[i].lon);
        }

        const routeData = {
            waypoints: waypointsArray,
            time: "00:00:00",
            date: "1970-01-01",
            arrive_by: arriveBy,
            leg_preferences: [],
            use_own_bike: useOwnBike,
            mode: "",
            max_transfers: maxTransfers,
            selected_modes: selectedModes,
            max_bike_distance: maxBikeDistance,
            bike_average_speed: bikeAverageSpeed,
            max_bikesharing_distance: maxBikesharingDistance,
            bikesharing_average_speed: bikesharingAverageSpeed,
            max_walk_distance: maxWalkDistance,
            walk_average_speed: walkAverageSpeed,
            bikesharing_lock_time: bikesharingLockTime,
            bike_lock_time: bikeLockTime,
            route_preference: preference
        }

        const result = await fetch(`${API_BASE_URL}/changeBikeStation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origin_bike_station: originBikeStation,
                new_index: bikeStationIndex,
                bike_stations: bikeStations,
                legs: legs,
                leg_index: legIndex,
                modes: modes,
                original_legs: originalLegs,
                route_data: routeData,
                bike_rack: legs[legIndex].bikeStationInfo?.rack
            })
        });

        const response = await result.json();

        const temporaryResults = [...results]
        temporaryResults[resultActiveIndex].tripPatterns[selectedTripPatternIndex] = response;

        setResults(temporaryResults);
    };


    const [zoom, setZoom] = useState<number>(0);
    const [showBikeStations, setShowBikeStations] = useState<boolean[]>([]);

    useMapEvent("zoomend", (e) => {
        setZoom(e.target.getZoom());
    });
    
    useEffect(() => {
        const currentLegs = results[resultActiveIndex]?.tripPatterns?.[selectedTripPatternIndex]?.legs ?? [];
        if (currentLegs.length > 0) {
            setShowBikeStations(currentLegs.map(() => false));
        }
    }, [results, resultActiveIndex, selectedTripPatternIndex]);

    if (!showResults) {
        return null;
    }


    const invertBikeStationAtIndex = (index: number) => {
        setShowBikeStations(prev => prev.map((v, i) => (i === index ? !v : v)));
    };

    return (
        <>
            {results[resultActiveIndex]?.tripPatterns?.[selectedTripPatternIndex]?.legs.map((leg, index) => {
                if (!leg || leg.mode !== "wait" || !leg?.bikeStationInfo) {
                    return null;
                }

                const origin = leg.bikeStationInfo.origin
                const color = origin ? 'green' : 'blue';
                const selectedIndex = leg.bikeStationInfo.selectedBikeStationIndex;
                const rack = leg.bikeStationInfo.rack;
                return (
                    <>
                        <CircleMarker
                            center={[leg.bikeStationInfo.latitude, leg.bikeStationInfo.longitude]}
                            radius={8}
                            pathOptions={{ color: color}}
                        >
                            <Popup autoPan={false}>
                                <button
                                    onClick={() => invertBikeStationAtIndex(index)}    
                                >
                                    {showBikeStations[index] ? "Hide bike stations" : "Show bike stations"}
                                </button>
                            </Popup>

                        </CircleMarker>
                        {showBikeStations[index] && leg?.bikeStationInfo.bikeStations.map((station, bikeStationIndex) => 
                            bikeStationIndex !== selectedIndex && zoom > 12 &&(
                                <CircleMarker
                                    center={[station.place.latitude, station.place.longitude]}
                                    radius={5}
                                    pathOptions={{ color: color }}
                                >
                                    <Popup autoPan={false}>
                                        Index: {bikeStationIndex} <br/>
                                        Score: {station.score} <br/>
                                        Distance: {station.distance} <br/>
                                        {rack ? (
                                            <>Capacity:  {station.place?.capacity} <br/> </>
                                        ) : (
                                            <>BikesAvailable: {station.place.bikesAvailable} <br/> </>
                                        )}
                                        <button 
                                            className="popup-button"
                                            onClick={() => changeBikeStation(origin, bikeStationIndex, leg.bikeStationInfo?.bikeStations as any, index)}
                                        >
                                            Set as {origin ? "origin" : "destination"} bike station
                                        </button>
                                    </Popup>
                                </CircleMarker>
                            )
                        )}
                    </>
                )
            })}
        </>
    );
}

export default BikeStations;

/** End of file BikeStations.tsx */
