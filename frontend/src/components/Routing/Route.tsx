/**
 * @file Route.tsx
 * @brief Hook responsible for route computation and request handling
 * @author Andrea Svitkova (xsvitka00)
 */

import { API_BASE_URL } from "../config/config";
import { useInput } from "../InputContext";
import { useResult } from "../ResultContext";
import { useSettings } from "../SettingsContext";
import dayjs from "dayjs";
import { storeWaypoints } from "../Sidebar/Planning/InputPoints/WaypointStorage";

/**
 * Hook for computing a route based on current application state
 * 
 * @returns Async function triggering route computation
 */
export function useRoute() {
    // Input context
    const {
        waypoints,
        mode, setMode,
        legPreferences,
        arriveBy,
        useOwnBike,
        preference,
        date,
        time,
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
        bikeLockTime
    } = useSettings();

    // Results context
    const {
        resultActiveIndex, setResultActiveIndex,
        results, setResults,
        setShowResults,
    } = useResult();

    /**
     * Sends a routing request to the backend and updates application state
     */
    const route = async () => {
        if (!results[resultActiveIndex].active) {
            let resultIndex = resultActiveIndex;
            let newMode = mode;

            // Convert waypoints to to compatible format
            let waypointsArray: string[] = [];
            for (let i = 0; i < waypoints.length; i++) {
                waypointsArray.push(waypoints[i].lat + ', ' + waypoints[i].lon);
            }

            // Prepare leg preference configuration
            let legPreferencesArray = [];
            const firstPref = legPreferences[0].mode;
            let equalPrefs = firstPref !== "transit,bicycle,walk";
            for (let i = 0; i < legPreferences.length; i++) {
                if (legPreferences[i].mode !== firstPref) {
                    equalPrefs = false;
                }
                legPreferencesArray.push({
                    mode: legPreferences[i].mode,
                    wait: legPreferences[i].wait.hour()*3600 + legPreferences[i].wait.minute()*60 + legPreferences[i].wait.second()
                });
            }

            // Adjust preferences for repeated routing
            const firstRouting = !results.some(result => result.active);
            if (!firstRouting && equalPrefs) {
                legPreferencesArray = Array.from(
                    { length: legPreferences.length },
                    () => ({ mode: "transit,bicycle,walk", wait: 0 })
                );
                equalPrefs = false;
            }

            // Determine routing mode and target result index
            if (equalPrefs) {
                newMode = firstPref;
                if (firstPref === "foot") {
                    resultIndex = 3;
                }
                else if (firstPref === "bicycle") {
                    resultIndex = 2;
                }
                else {
                    resultIndex = 1;
                }
            }

            // Send routing request to backend
            const result = await fetch(`${API_BASE_URL}/route`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    waypoints: waypointsArray,
                    time: time.format('HH:mm:ss'),
                    date: date.format('YYYY-MM-DD'),
                    arrive_by: arriveBy,
                    leg_preferences: legPreferencesArray,
                    use_own_bike: useOwnBike,
                    mode: mode,
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
                })
            });

            const newResult = await result.json();

            // Save waypoints to LocalStorage
            storeWaypoints(waypoints);

            // Store routing result
            setResults(prev => 
                prev.map((originalResult, index) => 
                    index === resultIndex ? newResult : originalResult
            ));
            setShowResults(true);

            setResultActiveIndex(resultIndex);
            setMode(newMode);
        }
    };
    return route;
}

/** End of file Route.tsx */
