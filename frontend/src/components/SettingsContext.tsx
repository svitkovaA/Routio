/**
 * @file SettingsContext.tsx
 * @brief 
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"

type SettingsContextType = {
    maxTransfers: number;
    setMaxTransfers: (value: number | ((prev: number) => number)) => void;
    selectedModes: string[];
    setSelectedModes: (value: string[] | ((prev: string[]) => string[])) => void;
    maxBikeDistance: number;
    setMaxBikeDistance: (value: number | ((prev: number) => number)) => void;
    bikeAverageSpeed: number;
    setBikeAverageSpeed: (value: number | ((prev: number) => number)) => void;
    maxBikesharingDistance: number;
    setMaxBikesharingDistance: (value: number | ((prev: number) => number)) => void;
    bikesharingAverageSpeed: number;
    setBikesharingAverageSpeed: (value: number | ((prev: number) => number)) => void;
    maxWalkDistance: number;
    setMaxWalkDistance: (value: number | ((prev: number) => number)) => void;
    walkAverageSpeed: number;
    setWalkAverageSpeed: (value: number | ((prev: number) => number)) => void;
    bikesharingLockTime: number;
    setBikesharingLockTime: (value: number | ((prev: number) => number)) => void;
    bikeLockTime: number;
    setBikeLockTime: (value: number | ((prev: number) => number)) => void;
    selectedLayerIndex: number;
    setSelectedLayerIndex: (layer: number) => void;
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

function useSettingsFromLocalStorage<T>(key: string, defaultValue: T) {
    const [value, setValue] = useState<T>(() => {
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : defaultValue;
    });

    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);

    return [value, setValue] as const;
}

export function SettingsProvider({ children } : {children: React.ReactNode}) {
    // Transport preferences
    const [maxTransfers, setMaxTransfers] = useSettingsFromLocalStorage("maxTransfers", 10);
    const defaultModes = ["bus", "tram", "rail", "trolleybus", "metro", "water"]
    const [selectedModes, setSelectedModes] = useSettingsFromLocalStorage<string[]>("selectedModes", defaultModes);
    
    // Cycling preferences
    const [maxBikeDistance, setMaxBikeDistance] = useSettingsFromLocalStorage("maxBikeDistance", 5);
    const [bikeAverageSpeed, setBikeAverageSpeed] = useSettingsFromLocalStorage("bikeAverageSpeed", 15);
    const [bikeLockTime, setBikeLockTime] = useSettingsFromLocalStorage("bikeLockTime", 2);

    // Bikesharing preferences
    const [maxBikesharingDistance, setMaxBikesharingDistance] = useSettingsFromLocalStorage("maxBikesharingDistance", 5);
    const [bikesharingAverageSpeed, setBikesharingAverageSpeed] = useSettingsFromLocalStorage("bikesharingAverageSpeed", 15);
    const [bikesharingLockTime, setBikesharingLockTime] = useSettingsFromLocalStorage("bikesharingLockTime", 5);

    // Walking preferences
    const [maxWalkDistance, setMaxWalkDistance] = useSettingsFromLocalStorage("maxWalkDistance", 5);
    const [walkAverageSpeed, setWalkAverageSpeed] = useSettingsFromLocalStorage("walkAverageSpeed", 5);
    
    const [selectedLayerIndex, setSelectedLayerIndex] = useState<number>(0);

    const value = useMemo(() => ({
        maxTransfers, setMaxTransfers,
        selectedModes, setSelectedModes,
        maxBikeDistance, setMaxBikeDistance,
        bikeAverageSpeed, setBikeAverageSpeed,
        maxBikesharingDistance, setMaxBikesharingDistance,
        bikesharingAverageSpeed, setBikesharingAverageSpeed,
        maxWalkDistance, setMaxWalkDistance,
        walkAverageSpeed, setWalkAverageSpeed,
        bikesharingLockTime, setBikesharingLockTime,
        bikeLockTime, setBikeLockTime,
        selectedLayerIndex, setSelectedLayerIndex
    }), [
        maxTransfers,
        selectedModes,
        maxBikeDistance,
        bikeAverageSpeed,
        maxBikesharingDistance,
        bikesharingAverageSpeed,
        maxWalkDistance,
        walkAverageSpeed,
        bikesharingLockTime,
        bikeLockTime,
        selectedLayerIndex
    ]);
    
    return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
    const ctx = useContext(SettingsContext);
    if (!ctx) {
        throw new Error("useSettings must be used within SettingsProvider");
    }
    return ctx;
}

/** End of file SettingsContext.tsx */
