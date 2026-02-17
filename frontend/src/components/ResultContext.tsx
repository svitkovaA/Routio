/**
 * @file ResultContext.tsx
 * @brief Provides global state management for route search results
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import { ResultsType, TripPattern, VehiclePosition } from "./types/types";
import { API_BASE_URL } from "./config/config";

type ResultContextType = {
    pattern: TripPattern;
    result: ResultsType;
    results: ResultsType[];
    setResults: (value: ResultsType[] | ((prev: ResultsType[]) => ResultsType[])) => void;
    resultActiveIndex: number;
    setResultActiveIndex: (value: number) => void;
    selectedTripPatternIndex: number;
    setSelectedTripPatternIndex: (value: number | ((prev: number) => number)) => void;
    showResults: boolean;
    setShowResults: (value: boolean) => void;
    showDetail: boolean;
    setShowDetail: (value: boolean) => void;
    showDepartures: boolean;
    showSettings: boolean;
    setShowSettings: (value: boolean) => void;
    loading: boolean;
    setLoading: (value: boolean) => void;
    vehiclePositions: VehiclePosition[];
    publicLegIndex: number;
    setPublicLegIndex: (value: number) => void;
    closeResults: () => void;
    abortRef: React.RefObject<AbortController | null>;
    mobileSidebarHeight: number;
    setMobileSidebarHeight: (value: number) => void;
};

const ResultContext = createContext<ResultContextType | undefined>(undefined);

export function ResultProvider({ children } : {children: React.ReactNode}) {

    // Array of result containers (one result for each result tab)
    const [results, setResults] = useState<ResultsType[]>(Array(4).fill({tripPatterns: [], active: false}));
    
    // Index of currently active result
    const [resultActiveIndex, setResultActiveIndex] = useState<number>(-1);

    // Index of selected trip pattern
    const [selectedTripPatternIndex, setSelectedTripPatternIndex] = useState<number>(0);

    // Controls visibility of results panel
    const [showResults, setShowResults] = useState(false);

    // Controls visibility of detailed trip view
    const [showDetail, setShowDetail] = useState<boolean>(false);

    // Controls visibility of departure alternatives
    const [showDepartures, setShowDepartures] = useState<boolean>(false);

    // Controls visibility of settings panel
    const [showSettings, setShowSettings] = useState(false);

    // Indicates whether route search request is currently loading
    const [loading, setLoading] = useState<boolean>(false);

    // Current vehicle positions
    const [vehiclePositions, setVehiclePositions] = useState<VehiclePosition[]>([]);

    // Index of public transport leg being recalculated
    const [publicLegIndex, setPublicLegIndex] = useState<number>(-1);

    // Stores the current height of the sidebar on mobile phones
    const [mobileSidebarHeight, setMobileSidebarHeight] = useState(0);

    // Stores previous vehicle positions for animation interpolation
    const prevPositionsRef = useRef<Record<number, VehiclePosition>>({});

    // Interval reference for periodic data polling
    const intervalRef = useRef<NodeJS.Timer | null>(null);

    // Reference to current animation frame request
    const animationRef = useRef<number | null>(null);

    // AbortController reference for cancelling ongoing API requests
    const abortRef = useRef<AbortController | null>(null);

    /**
     * Resets entire result state and stops all active processes
     */
    const closeResults = useCallback(() => {
        setShowResults(false);
        setResults(prev => prev.map(result => ({...result, active: false, tripPatterns: [], originBikeStations: [], destinationBikeStations: []})));
        setShowDetail(false);
        setSelectedTripPatternIndex(0);
        setLoading(false);
        setVehiclePositions([]);
        setResultActiveIndex(-1);

        // Clear previously stored vehicle positions
        prevPositionsRef.current = {};

        // Stop periodic polling
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        // Cancel active animation frame if running
        if (animationRef.current !== null) {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = null;
        }

        // Abort ongoing API request
        if (abortRef.current) {
            abortRef.current.abort();
            abortRef.current = null;
        }
    }, []);

    const value = useMemo(() => ({
        pattern: results[resultActiveIndex]?.tripPatterns[selectedTripPatternIndex],
        result: results[resultActiveIndex],
        results, setResults,
        resultActiveIndex, setResultActiveIndex,
        selectedTripPatternIndex, setSelectedTripPatternIndex,
        showResults, setShowResults,
        showDetail, setShowDetail,
        showDepartures,
        showSettings, setShowSettings,
        loading, setLoading,
        vehiclePositions,
        publicLegIndex, setPublicLegIndex,
        closeResults,
        abortRef,
        mobileSidebarHeight, setMobileSidebarHeight
    }), [
        results,
        resultActiveIndex,
        selectedTripPatternIndex,
        showResults,
        showDetail,
        showDepartures,
        showSettings,
        loading,
        vehiclePositions,
        publicLegIndex,
        closeResults,
        mobileSidebarHeight
    ]);

    /**
     * Performs linear interpolation between two values
     * 
     * @param a Starting value
     * @param b Target value
     * @param t Interpolation factor (0-1)
     */
    const linearInterpolation = useCallback((a: number, b: number, t: number) => {
        return a + (b - a) * t;
    }, []);

    /**
     * Animates transition between previous and new vehicle positions
     * 
     * @param from Previous vehicle position on map
     * @param to New vehicle position on map
     * @param duration Animation duration in milliseconds
     */
    const animatePositions = useCallback((
        from: Record<number, VehiclePosition>,
        to: Record<number, VehiclePosition>,
        duration = 2000
    ) => {
        const start = performance.now();

        // Cancel any currently running animation
        if (animationRef.current !== null) {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = null;
        }

        function frame(now: number) {
            const t = Math.min((now - start) / duration, 1);
            const interpolated: VehiclePosition[] = [];

            // Interpolate each vehicle position
            for (const tripId in to) {
                const prev = from[tripId];
                const next = to[tripId];

                // If no previous position exists, render directly
                if (!prev) {
                    interpolated.push(next);
                } else {
                    interpolated.push({
                        ...next,
                        lat: linearInterpolation(prev.lat, next.lat, t),
                        lon: linearInterpolation(prev.lon, next.lon, t)
                    });
                }
            }

            // Update state with interpolated vehicle positions
            setVehiclePositions(interpolated);

            // Continue animation until interpolation completes
            if (t < 1) {
                animationRef.current = requestAnimationFrame(frame);
            }
        }
        // Start animation loop
        animationRef.current = requestAnimationFrame(frame);
    }, [linearInterpolation]);

    // Currently selected trip pattern
    const pattern = value.pattern;

    /**
     * Extracts trip ids for which vehicle positions data should be requested
     */
    const tripIds = useMemo(
        () => pattern?.vehiclePositions?.map(p => p.tripId) ?? [],
        [pattern]
    );

    /**
     * Fetches vehicle positions from backend API
     */
    const fetchPositions = useCallback(async () => {
        if (!pattern) {
            return;
        }

        // Request with trip ids
        const res = await fetch(`${API_BASE_URL}/vehiclePositions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tripIds)
        });

        const realtime: Record<number, { lat: number; lon: number }> = await res.json();

        // Build next position map
        const nextMap: Record<number, VehiclePosition> = {};
        for (const v of pattern.vehiclePositions) {
            const pos = realtime[v.tripId];

            // Skip if no dat available for this trip
            if (!pos) {
                continue;
            }

            nextMap[v.tripId] = {
                ...v,
                lat: pos.lat,
                lon: pos.lon
            };
        }

        // If this is the first fetch update vehicle positions immediately
        if (Object.keys(prevPositionsRef.current).length === 0) {
            setVehiclePositions(Object.values(nextMap));
        }
        // Animate new vehicle positions
        else {
            animatePositions(prevPositionsRef.current, nextMap);
        }

        // Store current positions for next animation cycle
        prevPositionsRef.current = nextMap;
    }, [pattern, tripIds, animatePositions]);

    /**
     * Initializes and manages periodic polling of vehicle positions data
     */
    useEffect(() => {
        // Reset vehicle positions and clear stored ones
        setVehiclePositions([]);
        prevPositionsRef.current = {};

        // Stop existing polling interval
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        // Cancel running animation frame
        if (animationRef.current !== null) {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = null;
        }

        // Do not initialize polling if no valid pattern is selected
        if (selectedTripPatternIndex === -1 || !pattern)
            return;

        // Fetch current vehicle positions
        fetchPositions();

        // Start periodic polling of vehicle positions every 10 seconds
        intervalRef.current = setInterval(fetchPositions, 10000);

        // Ensures interval is properly cleared
        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [selectedTripPatternIndex, fetchPositions, pattern]);

    /**
     * Toggles departure visibility when public transport leg is selected
     */
    useEffect(() => setShowDepartures(publicLegIndex !== -1), [publicLegIndex]);

    return <ResultContext.Provider value={value}>{children}</ResultContext.Provider>;
}

export function useResult() {
    const ctx = useContext(ResultContext);
    if (!ctx) {
        throw new Error("useResult must be used within ResultProvider");
    }
    return ctx;
}

/** End of file ResultContext.tsx */
