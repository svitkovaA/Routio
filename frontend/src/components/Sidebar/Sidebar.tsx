/**
 * @file Sidebar.tsx
 * @brief Displays the sidebar component, handles routing requests, and switches between different sidebar views
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from 'react';
import dayjs from "dayjs";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { API_BASE_URL } from "../config/config";
import { LegPreference, Mode, ResultsType, RoutePreference, Waypoint } from '../types/types';
import Planning from './Planning/Planning';
import Settings from './Settings/Settings';
import Info from './Info/Info';
import Results from './Results/Results';
import './Sidebar.css';

type sidebarProps = {
    sidebarOpen: boolean;
    setSidebarOpen: (value: boolean) => void;
    waypoints: Waypoint[];
    setWaypoints: (value: Waypoint[] | ((prev: Waypoint[]) => Waypoint[])) => void;
    setMapSelectionIndex: (value: number) => void;
    results: ResultsType[];
    setResults: (value: ResultsType[] | ((prev: ResultsType[]) => ResultsType[])) => void;
    closeResults: () => void;
    showResults: boolean;
    setShowResults: (value: boolean) => void;
    resultActiveIndex: number;
    setResultActiveIndex: (value: number) => void;
    showInfo: boolean;
    selectedTripPatternIndex: number;
    setSelectedTripPatternIndex: (value: number | ((prev: number) => number)) => void;
    setShowInfo: (value: boolean) => void;
    mode: Mode | undefined;
    setMode: (value: Mode | undefined) => void;
    showDetail: boolean;
    setShowDetail: (value: boolean) => void;
    activeField: number | null;
    setActiveField: (value: number | null) => void;
    legPreferences: LegPreference[];
    setLegPreferences: (modes: LegPreference[] | ((prev: LegPreference[]) => LegPreference[])) => void;
    clearWaypoint: (index: number, clearDisplayName: boolean) => void;
    removeWaypoint: (currentIndex: number) => void;
    arriveBy: boolean;
    setArriveBy: (value: boolean) => void;
    useOwnBike: boolean;
    setUseOwnBike: (value: boolean) => void;
    maxTransfers: number;
    setMaxTransfers: (value: number | ((prev: number) => number)) => void;
    selectedModes: string[];
    setSelectedModes: (value: string[] | ((prev: string[]) => string[])) => void;
    maxBikeDistance: number;
    setMaxBikeDistance: (value: number | ((prev: number) => number)) => void;
    bikeAverageSpeed: number;
    setBikeAverageSpeed: (value: number | ((prev: number) => number)) => void;
    maxBikesharingDistance: number;
    setMaxBikesharingDistance: (value: number | ((prev: number) => number)) => void;
    bikesharingAverageSpeed: number;
    setBikesharingAverageSpeed: (value: number | ((prev: number) => number)) => void;
    maxWalkDistance: number;
    setMaxWalkDistance: (value: number | ((prev: number) => number)) => void;
    walkAverageSpeed: number;
    setWalkAverageSpeed: (value: number | ((prev: number) => number)) => void;
    bikesharingLockTime: number;
    setBikesharingLockTime: (value: number | ((prev: number) => number)) => void;
    bikeLockTime: number;
    setBikeLockTime: (value: number | ((prev: number) => number)) => void;
    preference: RoutePreference;
    setPreference: (value: RoutePreference) => void;
    findButtonDisabled: boolean;
    disableFindButton: () => void;
};

function Sidebar({ 
    sidebarOpen, 
    setSidebarOpen, 
    waypoints, 
    setWaypoints, 
    setMapSelectionIndex,
    results,
    setResults,
    closeResults,
    showResults,
    setShowResults,
    resultActiveIndex,
    setResultActiveIndex,
    showInfo,
    selectedTripPatternIndex,
    setSelectedTripPatternIndex,
    setShowInfo,
    mode,
    setMode,
    showDetail,
    setShowDetail,
    activeField,
    setActiveField,
    legPreferences,
    setLegPreferences,
    clearWaypoint,
    removeWaypoint,
    arriveBy,
    setArriveBy, 
    useOwnBike,
    setUseOwnBike,
    maxTransfers,
    setMaxTransfers,
    selectedModes,
    setSelectedModes,
    maxBikeDistance,
    setMaxBikeDistance,
    bikeAverageSpeed,
    setBikeAverageSpeed,
    maxBikesharingDistance,
    setMaxBikesharingDistance,
    bikesharingAverageSpeed,
    setBikesharingAverageSpeed,
    maxWalkDistance,
    setMaxWalkDistance,
    walkAverageSpeed,
    setWalkAverageSpeed,
    bikesharingLockTime,
    setBikesharingLockTime,
    bikeLockTime,
    setBikeLockTime,
    preference,
    setPreference,
    findButtonDisabled,
    disableFindButton
}: sidebarProps) {
    const [showSettings, setShowSettings] = useState(false);
    const [date, setDate] = useState(() => dayjs());
    const [time, setTime] = useState(() => dayjs());

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
                    waypoints={waypoints}
                    setWaypoints={setWaypoints}
                    setMapSelectionIndex={setMapSelectionIndex}
                    closeSidebar={() => setSidebarOpen(false)}
                    selectMultimodalResult={() => {
                        setResultActiveIndex(0);
                        setMode("transit,bicycle,walk");
                    }}
                    legPreferences={legPreferences}
                    setLegPreferences={setLegPreferences}
                    time={time}
                    date={date}
                    setTime={setTime}
                    setDate={setDate}
                    arriveBy={arriveBy}
                    setArriveBy={setArriveBy}
                    useOwnBike={useOwnBike}
                    setUseOwnBike={setUseOwnBike}
                    activeField={activeField}
                    setActiveField={setActiveField}
                    clearWaypoint={clearWaypoint}
                    removeWaypoint={removeWaypoint}
                    preference={preference}
                    setPreference={setPreference}
                    findButtonDisabled={findButtonDisabled}
                    disableFindButton={disableFindButton}
                    style={{display: showSettings || showResults ? "none" : "block"}}
                />

                <Settings
                    closeSettings={() => setShowSettings(false)}
                    maxTransfers={maxTransfers}
                    setMaxTransfers={setMaxTransfers}
                    selectedModes={selectedModes}
                    setSelectedModes={setSelectedModes}
                    maxBikeDistance={maxBikeDistance}
                    setMaxBikeDistance={setMaxBikeDistance}
                    bikeAverageSpeed={bikeAverageSpeed}
                    setBikeAverageSpeed={setBikeAverageSpeed}
                    maxBikesharingDistance={maxBikesharingDistance}
                    setMaxBikesharingDistance={setMaxBikesharingDistance}
                    bikesharingAverageSpeed={bikesharingAverageSpeed}
                    setBikesharingAverageSpeed={setBikesharingAverageSpeed}
                    maxWalkDistance={maxWalkDistance}
                    setMaxWalkDistance={setMaxWalkDistance}
                    walkAverageSpeed={walkAverageSpeed}
                    setWalkAverageSpeed={setWalkAverageSpeed}
                    bikesharingLockTime={bikesharingLockTime}
                    setBikesharingLockTime={setBikesharingLockTime}
                    bikeLockTime={bikeLockTime}
                    setBikeLockTime={setBikeLockTime}
                    style={{display: showSettings ? "block" : "none"}}
                />

                <Info
                    closeInfo={() => setShowInfo(false)}
                    style={{display: showInfo ? "block" : "none"}}
                />

                <Results
                    closeResults={closeResults}
                    mode={mode}
                    setMode={setMode}
                    result={results[resultActiveIndex]}
                    setResults={setResults}
                    resultActiveIndex={resultActiveIndex}
                    setResultActiveIndex={setResultActiveIndex}
                    selectedTripPatternIndex={selectedTripPatternIndex}
                    setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                    showDetail={showDetail}
                    setShowDetail={setShowDetail}
                    waypoints={waypoints}
                    style={{display: showResults ? "block" : "none"}}
                />
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
