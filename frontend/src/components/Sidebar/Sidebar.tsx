/**
 * @file Sidebar.tsx
 * @brief Sidebar component that handles routing requests, and switches between different sidebar views
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import { useMediaQuery } from '@mui/material';
import Planning from './Planning/Planning';
import Settings from './Settings/Settings';
import Info from './Info/Info';
import Results from './Results/Results';
import { useInput } from '../InputContext';
import { useResult } from '../ResultContext';
import { useRoute } from '../Routing/Route';
import DragHandle from './DragHandle/DragHandle';
import './Sidebar.css';

type sidebarProps = {
    sidebarOpen: boolean;                       // State indicating whether the sidebar is open
    setSidebarOpen: (value: boolean) => void;   // Setter controlling sidebar visibility
    showInfo: boolean;                          // State indicating whether the information view is active
    setShowInfo: (value: boolean) => void;      // Setter controlling information panel visibility
};

function Sidebar({ 
    sidebarOpen, 
    setSidebarOpen, 
    showInfo,
    setShowInfo
}: sidebarProps) {
    // User input context
    const { mode, setMode, waypoints } = useInput();

    //Results context
    const {
        resultActiveIndex, setResultActiveIndex,
        showResults,
        showDetail,
        showDepartures,
        showSettings
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

    const sidebarRef = useRef<HTMLDivElement>(null);
    const isMobile = useMediaQuery("(max-width: 768px)");
    const dragging = useRef(false);
    const [translateY, setTranslateY] = useState<number>(0);

    const [sheetHeight, setSheetHeight] = useState(0);
    const prevClosedOffset = useRef<number | null>(null);
    const closedOffset = Math.max(0, sheetHeight - 58);

    useLayoutEffect(() => {
        if (!sidebarRef.current || !isMobile) return;

        const ro = new ResizeObserver(() => {
            const h = sidebarRef.current!.getBoundingClientRect().height;
            setSheetHeight(h);
        });

        ro.observe(sidebarRef.current);
        return () => ro.disconnect();
    }, [isMobile, showResults, showDetail, showInfo, waypoints]);

    useLayoutEffect(() => {
        if (!isMobile || sheetHeight === 0) return;

        const prev = prevClosedOffset.current;
        const next = closedOffset;

        if (prev === null) {
            prevClosedOffset.current = next;
            setTranslateY(sidebarOpen ? -next : 0);
            return;
        }

        setTranslateY(prevY => {
            const openness = prev === 0 ? 0 : (-prevY / prev);
            const newY = -openness * next;
            return Math.max(-next, Math.min(0, newY));
        });

        prevClosedOffset.current = next;
    }, [closedOffset, isMobile, sidebarOpen]);

    useEffect(() => setTranslateY(sidebarOpen ? -closedOffset : 0), [sidebarOpen]);

    return (
        <div 
            id="sidebar" 
            className={sidebarOpen ? (showInfo ? "open open-info" : "open") : ""}
            style={{
                transform: isMobile
                    ? `translateY(${closedOffset + translateY}px)`
                    : undefined,
                transition: dragging.current ? undefined : "transform 0.3s ease",
            }}
            ref={sidebarRef}
        >
            <div className={"content-wrapper " + (showResults ? "results-open " : "") + (showDetail ? "detail-open " : "") + (showDepartures ? "more-departures-open" : "")}>
                {/* Planning view */}
                {!showSettings && !showResults && (
                    <Planning 
                        showInfo={() => setShowInfo(true)}
                        closeSidebar={() => setSidebarOpen(false)}
                        selectMultimodalResult={() => {
                            setResultActiveIndex(0);
                            setMode("transit,bicycle,walk");
                        }}
                    />
                )}

                {/* Settings view */}
                {showSettings && <Settings/>}

                {/* Info view */}
                {showInfo && (
                    <Info closeInfo={() => setShowInfo(false)} />
                )}

                {/* Results view */}
                {showResults && <Results/>}
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
            {isMobile && (
                <DragHandle 
                    translateY={translateY}
                    setTranslateY={setTranslateY}
                    dragging={dragging}
                    maxDrag={closedOffset}
                    sidebarOpen={sidebarOpen}
                    setSidebarOpen={setSidebarOpen}
                />
            )}
        </div>
    );
}

export default Sidebar;

/** End of file Sidebar.tsx */
