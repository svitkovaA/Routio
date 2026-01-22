/**
 * @file Sidebar.tsx
 * @brief Sidebar component that handles routing requests, and switches between different sidebar views
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef, useState } from 'react';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import Planning from './Planning/Planning';
import Settings from './Settings/Settings';
import Info from './Info/Info';
import Results from './Results/Results';
import { useInput } from '../InputContext';
import { useResult } from '../ResultContext';
import { useRoute } from '../Routing/Route';
import './Sidebar.css';
import L from 'leaflet';

type sidebarProps = {
    sidebarOpen: boolean;                       // State indicating whether the sidebar is open
    setSidebarOpen: (value: boolean) => void;   // Setter controlling sidebar visibility
    closeResults: () => void;                   // Closes routing results
    showInfo: boolean;                          // State indicating whether the information view is active
    setShowInfo: (value: boolean) => void;      // Setter controlling information panel visibility
};

function Sidebar({ 
    sidebarOpen, 
    setSidebarOpen,  
    closeResults,
    showInfo,
    setShowInfo
}: sidebarProps) {
    // State controlling settings view
    const [showSettings, setShowSettings] = useState(false);

    // User input context
    const { mode, setMode } = useInput();

    //Results context
    const {
        resultActiveIndex, setResultActiveIndex,
        showResults,
        showDetail,
    } = useResult();

    // Route context
    const route = useRoute();

    /**
     * Automatically triggers route computation when a routing mode and active
     * result index are set
     */
    useEffect(() => {
        if (mode && resultActiveIndex !== -1) {
            route();
        }
    }, [mode, resultActiveIndex]);

    return (
        <div 
            id="sidebar" 
            className={sidebarOpen ? (showInfo ? "open open-info" : "open") : ""}
        >
            <div className={"content-wrapper " + (showResults ? "results-open " : "") + (showDetail ? "detail-open" : "")}>
                {/* Planning view */}
                {!showSettings && !showResults && (
                    <Planning 
                        showSettings={() => setShowSettings(true)}
                        showInfo={() => setShowInfo(true)}
                        closeSidebar={() => setSidebarOpen(false)}
                        selectMultimodalResult={() => {
                            setResultActiveIndex(0);
                            setMode("transit,bicycle,walk");
                        }}
                    />
                )}

                {/* Settings view */}
                {showSettings && (
                    <Settings closeSettings={() => setShowSettings(false)} />
                )}

                {/* Info view */}
                {showInfo && (
                    <Info closeInfo={() => setShowInfo(false)} />
                )}

                {/* Results view */}
                {showResults && (
                    <Results closeResults={closeResults} />
                )}
            </div>

            {/* Sidebar toggle button */}
            <button 
                id="toggle-sidebar" 
                onClick={() => setSidebarOpen(!sidebarOpen)}
            >
                <KeyboardArrowLeftIcon 
                    fontSize="large" 
                    className={sidebarOpen ? "" : "rotate"}
                    sx={{ color: 'var(--color-text-primary)' }}
                />
            </button>

            {/* Clickable area for toggling sidebar */}
            <div 
                id="drag-sidebar" 
                onClick={() => setSidebarOpen(!sidebarOpen)}
            />
        </div>
    );
}

export default Sidebar;

/** End of file Sidebar.tsx */
