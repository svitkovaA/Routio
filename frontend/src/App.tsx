/**
 * @file App.tsx
 * @brief Main component of the application
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import { ThemeProvider } from "@mui/material/styles";
import { createTheme } from "@mui/material/styles";
import Map from './components/Map/Map';
import SideBar from './components/Sidebar/Sidebar';
import Controls from './components/Controls/Controls';
import { useInput } from './components/InputContext';
import { useResult } from './components/ResultContext';
import Info from './components/Info/Info';
import './App.css';

function App() {
    // Context for handling results
    const { closeResults } = useResult();

    // Context for handling user input and waypoint manipulation
    const {
        waypoints,
        clearWaypoint,
        removeWaypoint
    } = useInput();

    // State controlling the visibility of the sidebar
    const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

    // State controlling the visibility of the information panel
    const [showInfo, setShowInfo] = useState(false);   

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

    const theme = createTheme({
        palette: {
            primary: {
                main: "#057f73",
            },
        },
    });

    return (
        <ThemeProvider theme={theme}>
            <div className="app">
                {/* Control panel with layer and language selection */}
                <Controls 
                    setShowInfo={setShowInfo}
                />
                {/* Map component with markers*/}
                <Map 
                    sidebarOpen={sidebarOpen}
                    openSidebar={() => setSidebarOpen(true)}
                    handleMarkerRemove={handleMarkerRemove}
                />
                {/* Sidebar component with the search form, results, and trip details */}
                <SideBar 
                    sidebarOpen={sidebarOpen}
                    setSidebarOpen={setSidebarOpen}
                    showInfo={showInfo}
                />
                {/* Information about the application */}
                {showInfo && (
                    <Info closeInfo={() => setShowInfo(false)} />
                )}
            </div>
        </ThemeProvider>
    );
}

export default App;

/** End of file App.tsx */
