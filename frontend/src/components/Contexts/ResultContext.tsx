/**
 * @file ResultContext.tsx
 * @brief Provides global state management for route search results
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react"
import { PolyInfo, ResultsType, TripPattern, VehiclePosition } from "../types/types";
import polyline from '@mapbox/polyline';
import { API_BASE_URL } from "../config/config";
import { computeAscent, computeDescent, computeElevation, resamplePolyline , smoothElevationForGraph} from "../Sidebar/Results/Detail/Elevation/ElevationUtils";

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
    vehicleRealtimeData: VehiclePosition[];
    publicLegIndex: number;
    setPublicLegIndex: (value: number) => void;
    closeResults: () => void;
    abortRef: React.RefObject<AbortController | null>;
    mobileSidebarHeight: number;
    setMobileSidebarHeight: (value: number) => void;
    polyInfo: PolyInfo[];
    polylineForceUpdate: number;
    elevationLegIndex: number | null;
    setElevationLegIndex: (v: number | null) => void;
    hoveredProfileIndex: number | null;
    setHoveredProfileIndex: (v: number | null) => void;
    showBikeStations: boolean[];
    setShowBikeStations: (value: boolean[] | ((prev: boolean[]) => boolean[])) => void;
    openElevation: (index: number, value: boolean) => void;
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
    const [vehicleRealtimeData, setVehiclePositions] = useState<VehiclePosition[]>([]);

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

    // Forces rerendering of map polylines when route geometry changes
    const [polylineForceUpdate, setPolylineForceUpdate] = useState<number>(0);

    // Stores route leg information extended with computed elevation data
    const [polyInfoWithElevation, setPolyInfoWithElevation] = useState<PolyInfo[]>([]);

    // Index of the currently hovered point in the elevation profile
    const [hoveredProfileIndex, setHoveredProfileIndex] = useState<number | null>(null);

    // Index of the route leg whose elevation profile is currently hovered
    const [elevationLegIndex, setElevationLegIndex] = useState<number | null>(null);

    // State handling visibility flags for alternative bike stations
    const [showBikeStations, setShowBikeStations] = useState<boolean[]>([]);

    /**
     * Resets entire result state and stops all active processes
     */
    const closeResults = useCallback(() => {
        setShowResults(false);
        setResults(prev =>
            prev.map(result => ({
                ...result,
                active: false,
                tripPatterns: [],
                originBikeStations: [],
                destinationBikeStations: []
            }))
        );
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

    // Currently selected trip pattern
    const pattern = results[resultActiveIndex]?.tripPatterns[selectedTripPatternIndex];

    /**
     * Computes and stores decoded polyline data for the selected trip pattern
     */
    const polyInfo = useMemo(() => {
        if (!pattern?.originalLegs) {
            return [];
        }

        return pattern.originalLegs.map((leg) => {
            // Decode main route polyline
            const coords = Array.isArray(leg.pointsOnLink.points)
                ? leg.pointsOnLink.points.flatMap((p) => polyline.decode(p))
                : polyline.decode(leg.pointsOnLink.points);

            // Decode inactive route segments
            const inactiveCoords = leg.pointsOnLink.inactivePoints.map((p) =>
                polyline.decode(p)
            );

            return {
                coords,
                inactiveCoords,
                mode: leg.mode || "unknown",
                color: leg.color || "#000000",
                // Walking and cycling routes are rendered as dashed lines
                pathOptions: leg.mode === "foot" || leg.mode === "bicycle" ? { dashArray: "5px, 5px" } : {},
                tripId: leg.tripId,
                elevationOpen: false
            };
        });
    }, [pattern?.originalLegs]);

    /**
     * Forces polyline rerender when route geometry changes
     */
    useEffect(() => {
        setPolylineForceUpdate(prev => prev + 1);
    }, [pattern?.originalLegs]);

    /**
     * Computes elevation profiles for legs (foot, bicycle)
     */
    useEffect(() => {
        // No geometry data
        if (!polyInfo.length) {
            setPolyInfoWithElevation([]);
            return;
        }

        async function compute() {

            const result = [];

            // Iterate over all legs
            for (let i = 0; i < polyInfo.length; i++) {
                // Basic polyline information for the leg
                const poly = polyInfo[i];

                // Original leg data received from the backend
                const leg = pattern?.originalLegs[i];
                if (!leg) {
                    continue;
                }

                // Elevation profile and statistics initialization
                let elevationProfile = undefined;
                let rawProfile = undefined;
                let totalAscent = undefined;
                let totalDescent = undefined;

                // Elevation is only supported for cycling or walking segments
                if (leg.mode === "bicycle" || (leg.mode === "foot" && leg.walkMode)) {
                    // Resample polyline coordinates so points are evenly spaced approximately every 40 meters
                    const sampled = resamplePolyline(poly.coords, 40);
    
                    // Fetch elevation values for each sampled point
                    rawProfile = await computeElevation(sampled);
    
                    // Calculate total ascent
                    totalAscent = computeAscent(rawProfile);

                    // Calculate total descent
                    totalDescent = computeDescent(rawProfile);
                    elevationProfile = smoothElevationForGraph(rawProfile);
                }

                // Store combined polyline and elevation information
                result.push({
                    ...poly,
                    elevationProfile,
                    totalAscent,
                    totalDescent
                });

            }

            setPolyInfoWithElevation(result);
        }

        compute();

    }, [polyInfo]);

    /**
     * Toggles visibility of elevation profile for a specific route leg
     * 
     * @param index Index of the leg the visibility will be toggled
     * @param value The new toggle value
     */
    const openElevation = (index: number, value: boolean) => {
        setPolyInfoWithElevation(prev => {
            const newPolyInfo = [...prev];
            newPolyInfo[index].elevationOpen = value;
            return newPolyInfo;
        });
    };

    const value = useMemo(() => ({
        pattern: pattern,
        result: results[resultActiveIndex],
        results, setResults,
        resultActiveIndex, setResultActiveIndex,
        selectedTripPatternIndex, setSelectedTripPatternIndex,
        showResults, setShowResults,
        showDetail, setShowDetail,
        showDepartures,
        showSettings, setShowSettings,
        loading, setLoading,
        vehicleRealtimeData,
        publicLegIndex, setPublicLegIndex,
        closeResults,
        abortRef,
        mobileSidebarHeight, setMobileSidebarHeight,
        polyInfo: polyInfoWithElevation,
        polylineForceUpdate,
        hoveredProfileIndex, setHoveredProfileIndex,
        elevationLegIndex, setElevationLegIndex,
        showBikeStations, setShowBikeStations,
        openElevation
    }), [
        results,
        resultActiveIndex,
        selectedTripPatternIndex,
        showResults,
        showDetail,
        showDepartures,
        showSettings,
        loading,
        vehicleRealtimeData,
        publicLegIndex,
        closeResults,
        mobileSidebarHeight,
        polyInfoWithElevation,
        polylineForceUpdate,
        hoveredProfileIndex,
        elevationLegIndex,
        showBikeStations
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

    /**
     * Extracts trip ids with start time for which vehicle positions data should be requested
     */
    const tripIds = useMemo(
        () => pattern?.vehicleRealtimeData?.map((p) => ({"trip_id": p.tripId, "start_time": p.startTime})) ?? [],
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
        const res = await fetch(`${API_BASE_URL}/vehicleRealtimeData`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tripIds)
        });

        const realtime: Record<number, { lat: number; lon: number, delay?: number }> = await res.json();

        // Build next position map
        const nextMap: Record<number, VehiclePosition> = {};
        for (const v of pattern.vehicleRealtimeData) {
            const pos = realtime[v.tripId];

            // Skip if no dat available for this trip
            if (!pos) {
                continue;
            }

            nextMap[v.tripId] = {
                ...v,
                lat: pos.lat,
                lon: pos.lon,
                delay: pos?.delay
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

        if (resultActiveIndex >= 0 && selectedTripPatternIndex >= 0) {
            setResults(prev => {
                const newResults = [...prev];
                for (const leg of newResults[resultActiveIndex].tripPatterns[selectedTripPatternIndex]?.originalLegs) {
                    if (!leg.tripId) {
                        continue;
                    }

                    const pos = realtime[leg.tripId];
                    if (!pos) {
                        continue;
                    }

                    leg.delay = pos.delay;
                }
                return newResults;
            });
        }

        // Store current positions for next animation cycle
        prevPositionsRef.current = nextMap;
    }, [pattern, tripIds, animatePositions, resultActiveIndex, selectedTripPatternIndex]);

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
