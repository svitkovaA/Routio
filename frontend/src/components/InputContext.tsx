/**
 * @file InputContext.tsx
 * @brief 
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useContext, useMemo, useState } from "react"
import { LegPreference, Mode, RoutePreference, Waypoint } from "./types/types";
import { DragEndEvent } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import dayjs from "dayjs";

type InputContextType = {
    waypoints: Waypoint[];
    setWaypoints: (value: Waypoint[] | ((prev: Waypoint[]) => Waypoint[])) => void;
    mode: Mode | undefined;
    setMode: (value: Mode | undefined) => void;
    arriveBy: boolean;
    setArriveBy: (value: boolean) => void;
    useOwnBike: boolean;
    setUseOwnBike: (value: boolean) => void;
    preference: RoutePreference;
    setPreference: (value: RoutePreference) => void;
    activeField: number | null;
    setActiveField: (value: number | null) => void;
    legPreferences: LegPreference[];
    setLegPreferences: (modes: LegPreference[] | ((prev: LegPreference[]) => LegPreference[])) => void;
    time: dayjs.Dayjs;
    setTime: (value: dayjs.Dayjs) => void;
    date: dayjs.Dayjs;
    setDate: (value: dayjs.Dayjs) => void;
    mapSelectionIndex: number;
    setMapSelectionIndex: (value: number) => void;
    clearWaypoint: (index: number, clearDisplayName: boolean) => void;
    removeWaypoint: (currentIndex: number) => void;
    onDragEnd: (event: DragEndEvent) => void;
    addWaypoint: (index: number) => void;
    swapWaypoints: () => void;
};

const InputContext = createContext<InputContextType | undefined>(undefined);

export function InputProvider({ children } : {children: React.ReactNode}) {

    const [waypoints, setWaypoints] = useState<Waypoint[]>([{
        lat: 0,
        lon: 0,
        displayName: "",
        isActive: false,
        id: Math.random().toString(36).substring(2,9)
    }, {
        lat: 0,
        lon: 0,
        displayName: "",
        isActive: false,
        id: Math.random().toString(36).substring(2,9)
    }]);

    const [mode, setMode] = useState<Mode | undefined>(undefined);

    const [arriveBy, setArriveBy] = useState<boolean>(false);
    const [useOwnBike, setUseOwnBike] = useState<boolean>(true);
    const [preference, setPreference] = useState<RoutePreference>("fastest");
    const [activeField, setActiveField] = useState<number | null>(null);

    const [legPreferences, setLegPreferences] = useState<LegPreference[]>([{
        mode: "transit,bicycle,walk",
        wait: dayjs().startOf("day"),
        open: false
    }]);

    const [date, setDate] = useState(() => dayjs());
    const [time, setTime] = useState(() => dayjs());

    const [mapSelectionIndex, setMapSelectionIndex] = useState<number>(-1);

    const clearWaypoint = (index: number, clearDisplayName: boolean) => {
        setWaypoints(prev => {
            const newWaypoints = [...prev];
            newWaypoints[index] = { 
                ...newWaypoints[index], 
                displayName: clearDisplayName ? "" : newWaypoints[index].displayName,
                isActive: false 
            };
            return newWaypoints;
        });
    };

    const removeWaypoint = (currentIndex: number) => {
        if (currentIndex === activeField) setActiveField(null);
        setLegPreferences(prev => {
            const newPrefs = [...prev];

            if (currentIndex === waypoints.length - 1) {
                newPrefs.splice(prev.length - 1, 1);
            } 
            else {
                newPrefs.splice(currentIndex, 1);
            }
            if (newPrefs.length === 1) {
                return [{
                    mode: "transit,bicycle,walk",
                    wait: dayjs().startOf("day"),
                    open: false
                }];
            }
            return newPrefs;
        });
        setWaypoints(prev => prev.filter((_, i) => i !== currentIndex));
    };

    const addWaypoint = (index: number) => {
        const newWaypoints = [...waypoints];
        newWaypoints.splice(index + 1, 0, {
            lat: 0,
            lon: 0,
            displayName: "",
            isActive: false,
            id: Math.random().toString(36).substring(2,9)
        });
        setWaypoints(newWaypoints);
        const newLegPreferences = [...legPreferences];
        newLegPreferences.splice(index + 1, 0, {
            mode: "transit,bicycle,walk",
            wait: dayjs().startOf("day"),
            open: false
        });
        setLegPreferences(newLegPreferences);
    };

    const swapWaypoints = () => {
        if (waypoints.length === 2) {
            setWaypoints(prev => [prev[1], prev[0]]);
        }
    };

    const onDragEnd = (event: DragEndEvent) => {
        const {active, over} = event;
        if (over && active.id !== over.id) {
            const oldIndex = waypoints.findIndex(w => w.id === active.id);
            const newIndex = waypoints.findIndex(w => w.id === over.id);
            setWaypoints(prev => arrayMove(prev, oldIndex, newIndex));
        }
    };

    const value = useMemo(() => ({
        waypoints, setWaypoints,
        mode, setMode,
        arriveBy, setArriveBy,
        useOwnBike, setUseOwnBike,
        preference, setPreference,
        activeField, setActiveField,
        legPreferences, setLegPreferences,
        time, setTime,
        date, setDate,
        mapSelectionIndex, setMapSelectionIndex,
        clearWaypoint,
        removeWaypoint,
        onDragEnd,
        addWaypoint,
        swapWaypoints
    }), [
        waypoints,
        mode,
        arriveBy,
        useOwnBike,
        preference,
        activeField,
        legPreferences,
        time,
        date,
        mapSelectionIndex,
        clearWaypoint,
        removeWaypoint,
        onDragEnd,
        addWaypoint,
        swapWaypoints
    ]);
    
    return <InputContext.Provider value={value}>{children}</InputContext.Provider>;
}

export function useInput() {
    const ctx = useContext(InputContext);
    if (!ctx) {
        throw new Error("useInput must be used within InputProvider");
    }
    return ctx;
}

/** End of file InputContext.tsx */
