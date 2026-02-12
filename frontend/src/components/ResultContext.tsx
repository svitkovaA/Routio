/**
 * @file ResultContext.tsx
 * @brief React context for managing route search results and realtime vehicle positions
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
};

const ResultContext = createContext<ResultContextType | undefined>(undefined);

export function ResultProvider({ children } : {children: React.ReactNode}) {

    const [results, setResults] = useState<ResultsType[]>(Array(4).fill({tripPatterns: [], active: false}));
    const [resultActiveIndex, setResultActiveIndex] = useState<number>(-1);
    const [selectedTripPatternIndex, setSelectedTripPatternIndex] = useState<number>(0);
    const [showResults, setShowResults] = useState(false);
    const [showDetail, setShowDetail] = useState<boolean>(false);
    const [showDepartures, setShowDepartures] = useState<boolean>(false);
    const [showSettings, setShowSettings] = useState(false);
    const [loading, setLoading] = useState<boolean>(false);
    const [vehiclePositions, setVehiclePositions] = useState<VehiclePosition[]>([]);
    // Index of leg being recalculated
    const [publicLegIndex, setPublicLegIndex] = useState<number>(-1);
    const prevPositionsRef = useRef<Record<number, VehiclePosition>>({});
    const intervalRef = useRef<NodeJS.Timer | null>(null);
    const animationRef = useRef<number | null>(null);

    const abortRef = useRef<AbortController | null>(null);

    const closeResults = useCallback(() => {
        setShowResults(false);
        setResults(prev => prev.map(result => ({...result, active: false, tripPatterns: [], originBikeStations: [], destinationBikeStations: []})));
        setShowDetail(false);
        setSelectedTripPatternIndex(0);
        setLoading(false);
        setVehiclePositions([]);
        setResultActiveIndex(-1);
        prevPositionsRef.current = {};
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        if (animationRef.current !== null) {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = null;
        }
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
        abortRef
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
        closeResults
    ]);

    const linearInterpolation = useCallback((a: number, b: number, t: number) => {
        return a + (b - a) * t;
    }, []);

    const animatePositions = useCallback((
        from: Record<number, VehiclePosition>,
        to: Record<number, VehiclePosition>,
        duration = 2000
    ) => {
        const start = performance.now();

        if (animationRef.current !== null) {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = null;
        }

        function frame(now: number) {
            const t = Math.min((now - start) / duration, 1);
            const interpolated: VehiclePosition[] = [];

            for (const tripId in to) {
                const prev = from[tripId];
                const next = to[tripId];

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

            setVehiclePositions(interpolated);

            if (t < 1) {
                animationRef.current = requestAnimationFrame(frame);
            }
        }

        animationRef.current = requestAnimationFrame(frame);
    }, [linearInterpolation]);
    const pattern = value.pattern;

    const tripIds = useMemo(
        () => pattern?.vehiclePositions?.map(p => p.tripId) ?? [],
        [pattern]
    );

    const fetchPositions = useCallback(async () => {
        if (!pattern) return;

        const res = await fetch(`${API_BASE_URL}/vehiclePositions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(tripIds)
        });

        const realtime: Record<number, { lat: number; lon: number }> = await res.json();

        const nextMap: Record<number, VehiclePosition> = {};

        for (const v of pattern.vehiclePositions) {
            const pos = realtime[v.tripId];
            if (!pos) continue;

            nextMap[v.tripId] = {
                ...v,
                lat: pos.lat,
                lon: pos.lon
            };
        }

        if (Object.keys(prevPositionsRef.current).length === 0) {
            setVehiclePositions(Object.values(nextMap));
        } else {
            animatePositions(prevPositionsRef.current, nextMap);
        }

        prevPositionsRef.current = nextMap;
    }, [pattern, tripIds, animatePositions]);

    useEffect(() => {
        setVehiclePositions([]);
        prevPositionsRef.current = {};
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        if (animationRef.current !== null) {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = null;
        }
        if (selectedTripPatternIndex === -1 || !pattern)
            return;

        fetchPositions();
        intervalRef.current = setInterval(fetchPositions, 10000);

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [selectedTripPatternIndex, fetchPositions, pattern]);

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
