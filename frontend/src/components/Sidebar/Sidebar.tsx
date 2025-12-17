/**
 * @file Sidebar.tsx
 * @brief Displays the sidebar component, handles routing requests, and switches between different sidebar views
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { API_BASE_URL } from "../config/config";
import Planning from './Planning/Planning';
import Settings from './Settings/Settings';
import Info from './Info/Info';
import Results from './Results/Results';
import { useSettings } from '../SettingsContext';
import { useInput } from '../InputContext';
import { useResult } from '../ResultContext';
import './Sidebar.css';

type sidebarProps = {
    sidebarOpen: boolean;
    setSidebarOpen: (value: boolean) => void;
    closeResults: () => void;
    showInfo: boolean;
    setShowInfo: (value: boolean) => void;
    findButtonDisabled: boolean;
    disableFindButton: () => void;
};

function Sidebar({ 
    sidebarOpen, 
    setSidebarOpen,  
    closeResults,
    showInfo,
    setShowInfo,
    findButtonDisabled,
    disableFindButton
}: sidebarProps) {
    const [showSettings, setShowSettings] = useState(false);

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
        showResults, setShowResults,
        showDetail,
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

    useEffect(() => {
        if (mode && resultActiveIndex !== -1) {
            route();
        }
    }, [mode, resultActiveIndex]);

    return (
        <div id="sidebar" className={sidebarOpen ? (showInfo ? "open open-info" : "open") : ""}>
            <div className={"content-wrapper " + (showResults ? "results-open " : "") + (showDetail ? "detail-open" : "")}>
                <Planning 
                    showSettings={() => setShowSettings(true)}
                    showInfo={() => setShowInfo(true)}
                    closeSidebar={() => setSidebarOpen(false)}
                    selectMultimodalResult={() => {
                        setResultActiveIndex(0);
                        setMode("transit,bicycle,walk");
                    }}
                    findButtonDisabled={findButtonDisabled}
                    disableFindButton={disableFindButton}
                    style={{display: showSettings || showResults ? "none" : "block"}}
                />

                {showSettings && (
                    <Settings
                        closeSettings={() => setShowSettings(false)}
                    />
                )}

                {showInfo && (
                    <Info
                        closeInfo={() => setShowInfo(false)}
                    />
                )}

                {showResults && (
                    <Results
                        closeResults={closeResults}
                    />
                )}
            </div>

            <button id="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
                <FontAwesomeIcon icon={faAngleLeft} className={sidebarOpen ? "" : "rotate"} />
            </button>
            <div id="drag-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}/>
        </div>
    );
}

export default Sidebar;

/** End of file Sidebar.tsx */
