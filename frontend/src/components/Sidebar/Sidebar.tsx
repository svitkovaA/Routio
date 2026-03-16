/**
 * @file Sidebar.tsx
 * @brief Sidebar component that handles routing requests, and switches between different sidebar views
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMediaQuery } from '@mui/material';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import Planning from './Planning/Planning';
import Settings from './Settings/Settings';
import Results from './Results/Results';
import DragHandle from './DragHandle/DragHandle';
import CustomTooltip from '../CustomTooltip/CustomTooltip';
import { useInput } from '../Contexts/InputContext';
import { useResult } from '../Contexts/ResultContext';
import './Sidebar.css';

type sidebarProps = {
    sidebarOpen: boolean;                       // Indicates whether sidebar is currently open
    setSidebarOpen: (value: boolean) => void;   // Controls sidebar visibility state
    showInfo: boolean;                          // Indicates whether information panel is active
};

function Sidebar({ 
    sidebarOpen, 
    setSidebarOpen, 
    showInfo,
}: sidebarProps) {
    // Translation function
    const { t } = useTranslation();

    // User input context
    const { waypoints } = useInput();

    //Results context
    const {
        showResults,
        showDetail,
        showDepartures,
        showSettings,
        loading,
        setMobileSidebarHeight
    } = useResult();

    // Reference to sidebar DOM element
    const sidebarRef = useRef<HTMLDivElement>(null);

    // Media query determining mobile layout
    const isMobile = useMediaQuery("(max-width: 767px)");

    // Tracks whether user is currently dragging the sidebar
    const dragging = useRef(false);

    // Current vertical translation value
    const [translateY, setTranslateY] = useState<number>(0);

    // Current measured height of sidebar content.
    const [sheetHeight, setSheetHeight] = useState(0);

    // Stores previous closed offset value
    const prevClosedOffset = useRef<number | null>(null);

    // Maximum vertical offset of the sidebar when fully opened
    const closedOffset = Math.max(0, sheetHeight - 58);

    // Stores previous loading state
    const prevLoadingRef = useRef(loading);

    /**
     * Opens sidebar after routing finishes loading
     */
    useEffect(() => {
        if (prevLoadingRef.current && !loading) {
            setSidebarOpen(true);
        }

        prevLoadingRef.current = loading;
    }, [loading, setSidebarOpen]);

    /**
     * Observes sidebar height changes on mobile devices
     */
    useLayoutEffect(() => {
        if (!sidebarRef.current || !isMobile) {
            return;
        }

        // Create ResizeObserver to monitor height changes
        const ro = new ResizeObserver(() => {
            const h = sidebarRef.current!.getBoundingClientRect().height;
            setSheetHeight(h);
        });

        // Start observing sidebar element
        ro.observe(sidebarRef.current);

        // Cleanup observer
        return () => ro.disconnect();
    }, [isMobile, showResults, showDetail, showInfo, waypoints]);

    /**
     * Recalculates vertical translation when sheet height changes
     */
    useLayoutEffect(() => {
        if (!isMobile || sheetHeight === 0) {
            return;
        }

        const prev = prevClosedOffset.current;
        const next = closedOffset;

        // First initialization
        if (prev === null) {
            prevClosedOffset.current = next;
            // Set initial translateY based on sidebar open state
            setTranslateY(sidebarOpen ? -next : 0);
            return;
        }

        // Preserve relative openness ratio when height changes
        setTranslateY(prevY => {
            // Calculate previous openness percentage
            const openness = prev === 0 ? 0 : (-prevY / prev);

            // Apply same openness ratio to new height
            const newY = -openness * next;

            // Clamp value to valid range
            return Math.max(-next, Math.min(0, newY));
        });

        // Store updated offset for next recalculation
        prevClosedOffset.current = next;
    }, [closedOffset, isMobile, sidebarOpen, sheetHeight]);

    /**
     * Synchronizes translateY position when sidebarOpen changes
     */
    useEffect(() => setTranslateY(sidebarOpen ? -closedOffset : 0), [sidebarOpen, closedOffset]);

    // UseEffect for the route to fit map bound
    useEffect(() => {
        if (!isMobile) {
            setMobileSidebarHeight(0);
            return;
        }

        if (sidebarOpen) {
            setMobileSidebarHeight(closedOffset);
        } else {
            setMobileSidebarHeight(0);
        }

    }, [sidebarOpen, closedOffset, isMobile, setMobileSidebarHeight]);

    return (
        <div 
            className={"sidebar " + (sidebarOpen ? (showInfo ? "open open-info" : "open") : "")}
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
                        closeSidebar={() => setSidebarOpen(false)}
                    />
                )}

                {/* Settings view */}
                {showSettings && <Settings/>}

                {/* Results view */}
                {showResults && <Results/>}
            </div>

            {/* Sidebar toggle button */}
            <CustomTooltip title={sidebarOpen ? t("tooltips.sidebar.closeSidebar") : t("tooltips.sidebar.openSidebar")}>
                <button 
                    className="toggle-sidebar" 
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                >
                    <KeyboardArrowLeftIcon 
                        fontSize="large" 
                        className={sidebarOpen ? "" : "rotate"}
                        sx={{ color: 'var(--color-text-primary)' }}
                    />
                </button>
            </CustomTooltip>

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
