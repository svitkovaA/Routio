/**
 * @file App.tsx
 * @brief Main component of the application
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import Map from './components/Map/Map';
import SideBar from './components/Sidebar/Sidebar';
import Controls from './components/Controls/Controls';
import { useInput } from './components/InputContext';
import { useResult } from './components/ResultContext';
import './App.css';

function App() {
    // Context for handling results
    const { clearResults } = useResult();

    // Context for handling user input and waypoint manipulation
    const {
        setMode,
        waypoints,
        clearWaypoint,
        removeWaypoint
    } = useInput();

    // State controlling the visibility of the sidebar
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

    // State controlling the visibility of the information panel
    const [showInfo, setShowInfo] = useState(false);   

    /**
     * Clears computed results and resets the application mode
     * Function called when the user modifies waypoints or returns to the main search form
     */
    const closeResults = () => {
        clearResults();
        setMode(undefined);
    };

    /**
     * If exactly two waypoints exist, the selected waypoint is cleared instead
     * of removed in order to preserve the basic route structure
     * 
     * @param index Index of the waypoint to be removed
     */
    const handleMarkerRemove = (index: number) => {
        if (waypoints.length === 2) {
            clearWaypoint(index, true);
        }
        else {
            removeWaypoint(index);
        }
        closeResults();
    };

    return (
        <div className="app">
            {/* Control panel with layer and language selection */}
            <Controls 
                showInfo={showInfo}
                closeInfo={() => setShowInfo(false)}
            />
            {/* Map component with markers*/}
            <Map 
                sidebarOpen={sidebarOpen}
                openSidebar={() => setSidebarOpen(true)}
                handleMarkerRemove={handleMarkerRemove}
                closeResults={closeResults}
            />
            {/* Sidebar component with the search form, results, and trip details */}
            <SideBar 
                sidebarOpen={sidebarOpen}
                setSidebarOpen={setSidebarOpen}
                closeResults={closeResults}
                showInfo={showInfo}
                setShowInfo={setShowInfo}
            />
        </div>
    );
}
export default App;

/** End of file App.tsx */
