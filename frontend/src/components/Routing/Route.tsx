/**
 * @file Route.tsx
 * @brief Hook responsible for route computation
 * @author Andrea Svitkova (xsvitka00)
 */

import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE_URL } from "../config/config";
import { useInput } from "../InputContext";
import { useResult } from "../ResultContext";
import { useSettings } from "../SettingsContext";
import { storeWaypoints } from "../Sidebar/Planning/InputPoints/WaypointStorage";
import { Mode } from "../types/types";
import { useNotification } from "../NotificationContext";

/**
 * Hook for computing a route based on current application state
 * 
 * @returns Async function triggering route computation
 */
export function useRoute() {
    // Translation function
    const { t } = useTranslation();
    
    // Input context
    const {
        waypoints,
        legPreferences,
        arriveBy,
        useOwnBike,
        preference,
        date,
        time
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
        setResultActiveIndex,
        results, setResults,
        setShowResults,
        setLoading,
        abortRef
    } = useResult();

    // Notification context
    const { showNotification } = useNotification();
    
    /**
     * Sends a routing request to the backend and updates application state
     */
    const route = useCallback(async (resultIndex: number) => {
        // Abort any running request
        if (abortRef.current) {
            abortRef.current.abort();
            abortRef.current = null;
            setLoading(false);
        }

        // Execute only if selected result is not already active
        if (!results[resultIndex].active) {
            setLoading(true);

            // Convert waypoints to to compatible format
            let waypointsArray: string[] = [];
            for (let i = 0; i < waypoints.length; i++) {
                waypointsArray.push(waypoints[i].lat + ', ' + waypoints[i].lon);
            }

            // Prepare leg preference configuration
            let legPreferencesArray = [];
            const firstPref = legPreferences[0].mode;
            let equalPrefs = firstPref !== "multimodal";
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
                    () => ({ mode: "multimodal", wait: 0 })
                );
                equalPrefs = false;
            }

            // Determine routing mode and target result index
            if (equalPrefs) {
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

            // Create new abort controller
            const controller = new AbortController();
            abortRef.current = controller;

            // Determine routing mode string expected by backend
            const mode: Mode = resultIndex === 0 ? "multimodal" : 
                resultIndex === 1 ? "walk_transit" :
                resultIndex === 2 ? "bicycle" : "foot";

            try {
                // Send routing request to backend
                const result = await fetch(`${API_BASE_URL}/route`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    signal: controller.signal,
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
                        walk_speed: walkAverageSpeed,
                        bikesharing_lock_time: bikesharingLockTime,
                        bike_lock_time: bikeLockTime,
                        route_preference: preference
                    })
                });

                if (!result.ok) {
                    throw new Error("Server error");
                }

                setShowResults(true);
            
                const newResult = await result.json();
    
                // Save waypoints to LocalStorage
                storeWaypoints(waypoints);
    
                // Store routing result
                setResults(prev => 
                    prev.map((originalResult, index) => 
                        index === resultIndex ? newResult : originalResult
                ));
    
                // Set result active index to the result index
                setResultActiveIndex(resultIndex);
            }
            catch (error: any) {
                // Ignore abort errors
                if (error.name === "AbortError") {
                    return;
                }
                
                showNotification(t("errors.serverOffline"), "error");
                console.error(error);
            }
            finally {
                // Reset loading state
                if (abortRef.current === controller) {
                    setLoading(false);
                    abortRef.current = null;
                }
            }
        }
    }, [waypoints, legPreferences, arriveBy, useOwnBike, preference, date, time, maxTransfers, selectedModes,
        maxBikeDistance,bikeAverageSpeed, maxBikesharingDistance, bikesharingAverageSpeed, maxWalkDistance, 
        walkAverageSpeed, bikesharingLockTime, bikeLockTime, results, abortRef, setLoading, setResultActiveIndex,
        setResults, setShowResults, showNotification
    ]);
    return route;
}

/** End of file Route.tsx */
