/**
 * @file App.tsx
 * @brief Main application component
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import { LegPreference, Mode, ResultsType, RoutePreference, Waypoint } from './components/types/types';
import Map from './components/Map/Map';
import SideBar from './components/Sidebar/Sidebar';
import Controls from './components/Controls/Controls';
import './App.css';

function App() {
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
    const [waypoints, setWaypoints] = useState<Waypoint[]>([{
        lat: 0,
        lon: 0,
        displayName: "",
        isActive: false,
        id: Math.random().toString(36).substring(2,9)
    }, {
        lat: 0,
        lon: 0,
        displayName: "",
        isActive: false,
        id: Math.random().toString(36).substring(2,9)
    }]);
    const [mapSelectionIndex, setMapSelectionIndex] = useState<number>(-1);
    const [results, setResults] = useState<ResultsType[]>(Array(4).fill({tripPatterns: [], active: false}));
    const [resultActiveIndex, setResultActiveIndex] = useState<number>(-1);
    const [selectedTripPatternIndex, setSelectedTripPatternIndex] = useState<number>(0);
    const [selectedLayerIndex, setSelectedLayerIndex] = useState<number>(0);
    const [showResults, setShowResults] = useState(false);
    const [showInfo, setShowInfo] = useState(false);
    const [mode, setMode] = useState<Mode | undefined>(undefined);
    const [showDetail, setShowDetail] = useState<boolean>(false);
    const [activeField, setActiveField] = useState<number | null>(null);
    const [arriveBy, setArriveBy] = useState<boolean>(false);
    const [useOwnBike, setUseOwnBike] = useState<boolean>(true);
    const [maxTransfers, setMaxTransfers] = useState(10)
    const [selectedModes, setSelectedModes] = useState<string[]>([
        "bus",
        "tram",
        "rail",
        "trolleybus",
        "metro",
        "water"
    ]);
    const [maxBikeDistance, setMaxBikeDistance] = useState<number>(5);
    const [bikeAverageSpeed, setBikeAverageSpeed] = useState(15);
    const [maxBikesharingDistance, setMaxBikesharingDistance] = useState<number>(5);
    const [bikesharingAverageSpeed, setBikesharingAverageSpeed] = useState(15);
    const [maxWalkDistance, setMaxWalkDistance] = useState(5);
    const [walkAverageSpeed, setWalkAverageSpeed] = useState(5);
    const [bikesharingLockTime, setBikesharingLockTime] = useState<number>(5);
    const [bikeLockTime, setBikeLockTime] = useState<number>(2);
    const [preference, setPreference] = useState<RoutePreference>("fastest");
    const [findButtonDisabled, setFindButtonDisabled] = useState<boolean>(false);
    
    const [legPreferences, setLegPreferences] = useState<LegPreference[]>([{
        mode: "transit,bicycle,walk",
        exact: true,
        open: false
    }]);

    const closeResults = () => {
        setShowResults(false);
        setResults(prev => prev.map(result => ({...result, active: false, tripPatterns: [], originBikeStations: [], destinationBikeStations: []})));
        setMode(undefined);
        setShowDetail(false);
        setSelectedTripPatternIndex(0);
        setFindButtonDisabled(false);
    }
    
    const clearWaypoint = (index: number, clearDisplayName: boolean) => {
        setWaypoints(prev => {
            const newWaypoints = [...prev];
            newWaypoints[index] = { 
                ...newWaypoints[index], 
                displayName: clearDisplayName ? "" : newWaypoints[index].displayName,
                isActive: false 
            };
            return newWaypoints;
        });
    };

    const removeWaypoint = (currentIndex: number) => {
        if (currentIndex === activeField) setActiveField(null);
        setLegPreferences(prev => {
            const newPrefs = [...prev];

            if (currentIndex === waypoints.length - 1) {
                newPrefs.splice(prev.length - 1, 1);
            } 
            else {
                newPrefs.splice(currentIndex, 1);
            }
            if (newPrefs.length === 1) {
                return [{
                    mode: "transit,bicycle,walk",
                    exact: true,
                    open: false
                }];
            }
            return newPrefs;
        });
        setWaypoints(prev => prev.filter((_, i) => i !== currentIndex));
    };

    const handleMarkerRemove = (index: number) => {
        if (waypoints.length === 2) {
            clearWaypoint(index, true);
        }
        else {
            removeWaypoint(index);
        }
        closeResults();
    }

    return (
        <div className="app">
            <Controls 
                showInfo={showInfo}
                closeInfo={() => setShowInfo(false)}
                selectedLayerIndex={selectedLayerIndex}
                setSelectedLayerIndex={setSelectedLayerIndex}
            />
            <Map 
                sidebarOpen={sidebarOpen}
                openSidebar={() => setSidebarOpen(true)}
                waypoints={waypoints}
                setWaypoints={setWaypoints}
                mapSelectionIndex={mapSelectionIndex}
                setMapSelectionIndex={setMapSelectionIndex}
                results={results}
                setResults={setResults}
                resultActiveIndex={resultActiveIndex}
                showResults={showResults}
                selectedLayerIndex={selectedLayerIndex}
                selectedTripPatternIndex={selectedTripPatternIndex}
                handleMarkerRemove={handleMarkerRemove}
                arriveBy={arriveBy}
                useOwnBike={useOwnBike}
                maxTransfers={maxTransfers}
                selectedModes={selectedModes}
                maxBikeDistance={maxBikeDistance}
                bikeAverageSpeed={bikeAverageSpeed}
                maxBikesharingDistance={maxBikesharingDistance}
                bikesharingAverageSpeed={bikesharingAverageSpeed}
                maxWalkDistance={maxWalkDistance}
                walkAverageSpeed={walkAverageSpeed}
                bikesharingLockTime={bikesharingLockTime}
                bikeLockTime={bikeLockTime}
                preference={preference}
                setPreference={setPreference}
                closeResults={closeResults}
            />
            <SideBar 
                sidebarOpen={sidebarOpen}
                setSidebarOpen={setSidebarOpen}
                waypoints={waypoints}
                setWaypoints={setWaypoints}
                setMapSelectionIndex={setMapSelectionIndex}
                results={results}
                setResults={setResults}
                closeResults={closeResults}
                showResults={showResults}
                setShowResults={setShowResults}
                resultActiveIndex={resultActiveIndex}
                setResultActiveIndex={setResultActiveIndex}
                showInfo={showInfo}
                setShowInfo={setShowInfo}
                selectedTripPatternIndex={selectedTripPatternIndex}
                setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                mode={mode}
                setMode={setMode}
                showDetail={showDetail}
                setShowDetail={setShowDetail}
                activeField={activeField}
                setActiveField={setActiveField}
                legPreferences={legPreferences}
                setLegPreferences={setLegPreferences}
                clearWaypoint={clearWaypoint}
                removeWaypoint={removeWaypoint}
                arriveBy={arriveBy}
                setArriveBy={setArriveBy}
                useOwnBike={useOwnBike}
                setUseOwnBike={setUseOwnBike}
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
                preference={preference}
                setPreference={setPreference}
                findButtonDisabled={findButtonDisabled}
                disableFindButton={() => setFindButtonDisabled(true)}
            />  
        </div>
    );
}
export default App;

/** End of file App.tsx */
