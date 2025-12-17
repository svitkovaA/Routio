/**
 * @file App.tsx
 * @brief Main application component
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
    const { clearResults } = useResult();

    const {
        setMode,
        waypoints,
        clearWaypoint,
        removeWaypoint
    } = useInput();

    const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
    const [showInfo, setShowInfo] = useState(false);   

    const closeResults = () => {
        clearResults();
        setMode(undefined);
    };

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
            <Controls 
                showInfo={showInfo}
                closeInfo={() => setShowInfo(false)}
            />
            <Map 
                sidebarOpen={sidebarOpen}
                openSidebar={() => setSidebarOpen(true)}
                handleMarkerRemove={handleMarkerRemove}
                closeResults={closeResults}
            />
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
