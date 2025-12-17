import { API_BASE_URL } from "../config/config";
import { useInput } from "../InputContext";
import { useResult } from "../ResultContext";
import { useSettings } from "../SettingsContext";

export function useRoute() {
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
        resultActiveIndex, setResultActiveIndex,
        results, setResults,
        setShowResults,
    } = useResult();

    const route = async () => {
        console.log(results)
        console.log("resultIndex: " + resultActiveIndex);
        if (!results[resultActiveIndex].active) {
            let resultIndex = resultActiveIndex;
            let newMode = mode;
            let waypointsArray: string[] = [];
            for (let i = 0; i < waypoints.length; i++) {
                waypointsArray.push(waypoints[i].lat + ', ' + waypoints[i].lon);
            }

            let legPreferencesArray = [];
            const firstPref = legPreferences[0].mode;
            let equalPrefs = firstPref !== "transit,bicycle,walk";
            for (let i = 0; i < legPreferences.length; i++) {
                if (legPreferences[i].mode !== firstPref) {
                    equalPrefs = false;
                }
                legPreferencesArray.push({
                    mode: legPreferences[i].mode,
                    exact: legPreferences[i].exact
                });
            }

            const firstRouting = !results.some(result => result.active);
            if (!firstRouting && equalPrefs) {
                legPreferencesArray = Array.from(
                    { length: legPreferences.length },
                    () => ({ mode: "transit,bicycle,walk", exact: true })
                );
                equalPrefs = false;
            }

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
