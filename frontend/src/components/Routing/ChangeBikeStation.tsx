/**
 * @file ChangeBikeStation.tsx
 * @brief Hook for changing the selected bikesharing station within a route
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import { API_BASE_URL } from "../config/config";
import { useInput } from "../Contexts/InputContext";
import { useNotification } from "../Contexts/NotificationContext";
import { useResult } from "../Contexts/ResultContext";
import { useSettings } from "../Contexts/SettingsContext";
import type { BikeStation } from "../types/types";

/**
 * Hook that provides functionality for updating bikesharing station selection
 * within an already computed route
 */
export function useChangeBikeStation() {
    // Translation function
    const { t } = useTranslation();

    // User input context
    const {
        waypoints,
        arriveBy,
        useOwnBike,
        preference,
    } = useInput();

    // Settings context
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
        bikeLockTime,
        useHistoricalDelays
    } = useSettings();

    // Result context
    const { 
        pattern,
        results, setResults,
        resultActiveIndex,
        selectedTripPatternIndex
    } = useResult();

    // Notification context
    const { showNotification } = useNotification();

    /**
     * Requests route recalculation with a selected bikesharing station
     * 
     * @param originBikeStation True if the station is the origin station, false otherwise
     * @param bikeStationIndex Index of the newly selected bike station
     * @param bikeStations List of available bike stations
     * @param legIndex Index of the route leg being modified
     */
    const changeBikeStation = async (originBikeStation: boolean, bikeStationIndex: number, bikeStations: BikeStation[], legIndex: number) => {
        // Extract current route structure
        const originalLegs = pattern?.originalLegs;
        const modes = pattern.modes;
        
        // Convert waypoints to compatible format
        const waypointsArray: string[] = [];
        for (let i = 0; i < waypoints.length; i++) {
            waypointsArray.push(waypoints[i].lat + ', ' + waypoints[i].lon);
        }

        const originIndex = waypoints.findIndex(w => w.origin === true);
        const destinationIndex = waypoints.findIndex(w => w.origin === false);

        // Routing data
        const routeData = {
            waypoints: waypointsArray,
            time: "00:00:00",
            date: "1970-01-01",
            arrive_by: arriveBy,
            leg_preferences: [],
            use_own_bike: useOwnBike,
            mode: "multimodal", // Dummy value
            max_transfers: maxTransfers,
            selected_modes: selectedModes,
            max_bike_distance: maxBikeDistance,
            bike_average_speed: bikeAverageSpeed,
            max_bikesharing_distance: maxBikesharingDistance,
            bikesharing_average_speed: bikesharingAverageSpeed,
            max_walk_distance: maxWalkDistance,
            walk_speed: walkAverageSpeed,
            bikesharing_lock_time: bikesharingLockTime,
            bike_lock_time: bikeLockTime,
            route_preference: preference,
            use_historical_delays: useHistoricalDelays,
            origin_station: originIndex >= 0 ? {
                "index": originIndex,
                "id": waypoints[originIndex].bikeStationId
            } : null,
            destination_station: destinationIndex >= 0 ? {
                "index": destinationIndex,
                "id": waypoints[destinationIndex].bikeStationId
            } : null
        }

        try {
            // Send request to backend for route recalculation
            const result = await fetch(`${API_BASE_URL}/changeBikeStation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    origin_bike_station: originBikeStation,
                    new_index: bikeStationIndex,
                    bike_stations: bikeStations,
                    leg_index: legIndex,
                    modes: modes,
                    original_legs: originalLegs,
                    route_data: routeData
                })
            });
    
            // Change bike station failed
            if (!result.ok) {
                throw new Error("Change bike station failed");
            }
    
            const response = await result.json();
    
            // Update the active trip pattern in results
            const temporaryResults = [...results]
            temporaryResults[resultActiveIndex].tripPatterns[selectedTripPatternIndex] = response;
    
            setResults(temporaryResults);
        }
        catch {
            showNotification(t("errors.changeBikeStationFailed"), "error");
        }
    };
    return changeBikeStation;
}

/** ChangeBikeStation.tsx */
