/**
 * @file SettingsContext.tsx
 * @brief 
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useContext, useMemo, useState } from "react"

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

export function SettingsProvider({ children } : {children: React.ReactNode}) {

    const [maxTransfers, setMaxTransfers] = useState(10);
    const [selectedModes, setSelectedModes] = useState<string[]>([
        "bus",
        "tram",
        "rail",
        "trolleybus",
        "metro",
        "water"
    ]);
    const [maxBikeDistance, setMaxBikeDistance] = useState<number>(5);
    const [bikeAverageSpeed, setBikeAverageSpeed] = useState(15);
    const [maxBikesharingDistance, setMaxBikesharingDistance] = useState<number>(5);
    const [bikesharingAverageSpeed, setBikesharingAverageSpeed] = useState(15);
    const [maxWalkDistance, setMaxWalkDistance] = useState(5);
    const [walkAverageSpeed, setWalkAverageSpeed] = useState(5);
    const [bikesharingLockTime, setBikesharingLockTime] = useState<number>(5);
    const [bikeLockTime, setBikeLockTime] = useState<number>(2);
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
