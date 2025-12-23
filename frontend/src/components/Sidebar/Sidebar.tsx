/**
 * @file Sidebar.tsx
 * @brief Displays the sidebar component, handles routing requests, and switches between different sidebar views
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from 'react';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import Planning from './Planning/Planning';
import Settings from './Settings/Settings';
import Info from './Info/Info';
import Results from './Results/Results';
import { useInput } from '../InputContext';
import { useResult } from '../ResultContext';
import { useRoute } from '../Routing/Route';
import './Sidebar.css';

type sidebarProps = {
    sidebarOpen: boolean;
    setSidebarOpen: (value: boolean) => void;
    closeResults: () => void;
    showInfo: boolean;
    setShowInfo: (value: boolean) => void;
};

function Sidebar({ 
    sidebarOpen, 
    setSidebarOpen,  
    closeResults,
    showInfo,
    setShowInfo
}: sidebarProps) {
    const [showSettings, setShowSettings] = useState(false);
    const { mode, setMode } = useInput();
    const {
        resultActiveIndex, setResultActiveIndex,
        showResults,
        showDetail,
    } = useResult();

    const route = useRoute();

    useEffect(() => {
        if (mode && resultActiveIndex !== -1) {
            route();
        }
    }, [mode, resultActiveIndex]);

    return (
        <div id="sidebar" className={sidebarOpen ? (showInfo ? "open open-info" : "open") : ""}>
            <div className={"content-wrapper " + (showResults ? "results-open " : "") + (showDetail ? "detail-open" : "")}>
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

                {showSettings && (
                    <Settings closeSettings={() => setShowSettings(false)} />
                )}

                {showInfo && (
                    <Info closeInfo={() => setShowInfo(false)} />
                )}

                {showResults && (
                    <Results closeResults={closeResults} />
                )}
            </div>

            <button id="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
                <KeyboardArrowLeftIcon fontSize="large" className={sidebarOpen ? "" : "rotate"} />
            </button>
            <div id="drag-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}/>
        </div>
    );
}

export default Sidebar;

/** End of file Sidebar.tsx */
