/**
 * @file InputContext.tsx
 * @brief Provides global state management for user input parameters
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState, Dispatch, SetStateAction } from "react"
import { DragEndEvent } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import dayjs from "dayjs";
import { LegPreference, RoutePreference, Station, Waypoint } from "../types/types";
import { useResult } from "./ResultContext";
import { useSettingsFromLocalStorage } from "./SettingsContext";
import { API_BASE_URL } from "../config/config";

type InputContextType = {
    waypoints: Waypoint[];
    setWaypoints: (value: Waypoint[] | ((prev: Waypoint[]) => Waypoint[])) => void;
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
    fieldErrors: number[];
    setFieldErrors: Dispatch<SetStateAction<number[]>>;
    showBikeStations: boolean;
    setShowBikeStations: (value: boolean) => void;
    bikeStations: Station[];
};

const InputContext = createContext<InputContextType | undefined>(undefined);

export function InputProvider({ children } : {children: React.ReactNode}) {
    // Currently active result index
    const {
        resultActiveIndex,
        showResults
    } = useResult();

    // Waypoints initialization
    const [waypoints, setWaypoints] = useState<Waypoint[]>([{
        lat: 0,
        lon: 0,
        displayName: "",
        isActive: false,
        isPreview: false,
        id: Math.random().toString(36).substring(2,9),
        bikeStationId: null,
        origin: null
    }, {
        lat: 0,
        lon: 0,
        displayName: "",
        isActive: false,
        isPreview: false,
        id: Math.random().toString(36).substring(2,9),
        bikeStationId: null,
        origin: null
    }]);

    // Determines whether the selected time represents arrival time, or departure time
    const [arriveBy, setArriveBy] = useState<boolean>(false);

    // Indicates whether the user prefers using their own bicycle instead of shared bicycles
    const [useOwnBike, setUseOwnBike] = useSettingsFromLocalStorage<boolean>("useOwnBike", true);

    // Route optimization preference
    const [preference, setPreference] = useSettingsFromLocalStorage<RoutePreference>("routePreference", "fastest");

    // Index of the currently active input field
    const [activeField, setActiveField] = useState<number | null>(null);

    // Transport mode preferences per leg between waypoints
    const [legPreferences, setLegPreferences] = useState<LegPreference[]>([{
        mode: "multimodal",
        wait: dayjs().startOf("day"),
        open: false
    }]);

    // Selected travel date and time
    const [date, setDate] = useState(() => dayjs());
    const [time, setTime] = useState(() => dayjs());

    // Index of the waypoint currently being assigned via map click
    const [mapSelectionIndex, setMapSelectionIndex] = useState<number>(-1);

    // Stores indices of input fields that currently contain validation errors
    const [fieldErrors, setFieldErrors] = useState<number[]>([]);

    // Stores information about showing bicycle stations
    const [showBikeStations, setShowBikeStations] = useState<boolean>(false);

    // Stores bike stations
    const [bikeStations, setBikeStations] = useState<Station[]>([]);

    /**
     * Fetches bicycle stations
     */
    useEffect(() => {
        const loadStations = async () => {
            const apiResult = await fetch(`${API_BASE_URL}/bicycleStations`);
            const data = await apiResult.json();

            setBikeStations(data);
        }
        if (bikeStations.length === 0) {
            loadStations();
        }
    }, [showBikeStations, bikeStations]);

    /**
     * Unset mapSelectionIndex if other action occurs
     */
    useEffect(() => {
        setMapSelectionIndex(-1);
    }, [waypoints, time, date, preference, useOwnBike, arriveBy, legPreferences, resultActiveIndex]);

    /**
     * Hide bicycle stations when bicycle options are changed
     */
    useEffect(() => {
        setShowBikeStations(false);
    }, [useOwnBike, showResults]);

    /**
     * Remove information about stations from input form when bike options change
     */
    useEffect(() => {
        setWaypoints(prev => {
            return prev.map(w => ({
                ...w,
                bikeStationId: null,
                origin: null
            }));
        });
    }, [useOwnBike]);

    /**
     *  Clears waypoint at the specified index
     * 
     * @param index Index of the waypoint to clear
     * @param clearDisplayName If true, displayName is reset to an empty string
     */
    const clearWaypoint = useCallback((index: number, clearDisplayName: boolean) => {
        setWaypoints(prev => {
            const newWaypoints = [...prev];

            newWaypoints[index] = { 
                ...newWaypoints[index], 
                displayName: clearDisplayName ? "" : newWaypoints[index].displayName,
                isActive: false,
                bikeStationId: null,
                origin: null
            };

            return newWaypoints;
        });
    }, []);

    /**
     * Removes a waypoint at the specified index
     * 
     * @param index Index of the waypoint to remove
     */
    const removeWaypoint = useCallback((index: number) => {
        // If removed waypoint is the currently active one, clear focus
        if (index === activeField) {
            setActiveField(null);
        }

        // Update leg preferences to match the new waypoint structure
        setLegPreferences(prev => {
            const newPrefs = [...prev];

            // Removing the last waypoint removes the last leg preference
            if (index === waypoints.length - 1) {
                newPrefs.splice(prev.length - 1, 1);
            } 
            // Removing an intermediate waypoint removes the preference at the same index
            else {
                newPrefs.splice(index, 1);
            }

            // Restore default if only one preference remains
            if (newPrefs.length === 1) {
                return [{
                    mode: "multimodal",
                    wait: dayjs().startOf("day"),
                    open: false
                }];
            }

            return newPrefs;
        });
        // Remove waypoint entry from state
        setWaypoints(prev => prev.filter((_, i) => i !== index));

        // Removes the error for the deleted field and updates remaining error indices
        setFieldErrors(prev => prev.filter(i => i !== index).map(i => i > index ? i - 1 : i)
    );
    }, [activeField, waypoints.length]);

    /**
     * Inserts a new waypoint after the specified index
     * 
     * @param index Index after which the new waypoint will be inserted
     */
    const addWaypoint = useCallback((index: number) => {
        // Maximum available waypoints reached
        if (waypoints.length >= 10) {
            return;
        }

        // Insert new waypoint after the given index
        setWaypoints(prev => {
            if (prev.length >= 10) return prev;

            const updated = [...prev];
            updated.splice(index + 1, 0, {
                lat: 0,
                lon: 0,
                displayName: "",
                isActive: false,
                isPreview: false,
                id: Math.random().toString(36).substring(2, 9),
                bikeStationId: null,
                origin: null
            });
            return updated;
        });

        // Insert default leg preference for the newly added segment
        setLegPreferences(prev => {
            const updated = [...prev];
            updated.splice(index + 1, 0, {
                mode: "multimodal",
                wait: dayjs().startOf("day"),
                open: false
            });
            return updated;
        });
        
        // Shift error indices forward after inserting a new field
        setFieldErrors(prev => prev.map(errorIndex => errorIndex >= index + 1 ? errorIndex + 1 : errorIndex));

    }, [waypoints]);

    /**
     * Swaps origin and destination waypoints
     */
    const swapWaypoints = useCallback(() => {
        if (waypoints.length === 2) {
            setWaypoints(prev => [prev[1], prev[0]]);

            // Update error indices to match swapped field positions
            setFieldErrors(prev => prev.map(i => i === 0 ? 1 : i === 1 ? 0 : i));
        }
    }, [waypoints.length]);

    /**
     * Handles drag and drop reordering of waypoints
     */
    const onDragEnd = useCallback((event: DragEndEvent) => {
        const {active, over} = event;

        // Ensure valid drop target
        if (over && active.id !== over.id) {
            // Determine original and new indices based on waypoint ids
            const oldIndex = waypoints.findIndex(w => w.id === active.id);
            const newIndex = waypoints.findIndex(w => w.id === over.id);

            // Create a reordered copy of waypoints based
            const reordered = arrayMove(waypoints, oldIndex, newIndex);

            // Reorder waypoints using arrayMove utility
            setWaypoints(prev => arrayMove(prev, oldIndex, newIndex));

            // Recalculate error indices after reordering
            setFieldErrors(prev =>
                prev.map(errorIndex => {
                    const waypointId = waypoints[errorIndex].id;
                    return reordered.findIndex(w => w.id === waypointId);
                })
            );
        }
    }, [waypoints]);

    /**
     * Updates leg preferences
     */
    useEffect(() => {
        setLegPreferences(prev => {
            // Find indices of origin and destination stations
            const originIndex = waypoints.findIndex(w => w.origin === true);
            const destinationIndex = waypoints.findIndex(w => w.origin === false);

            // Ensure correct station order
            if (originIndex >= 0 && destinationIndex >= 0 && originIndex > destinationIndex) {
                setWaypoints(prev => {
                    const updated = [...prev];
                    updated[originIndex].origin = false;
                    updated[destinationIndex].origin = true;
                    return updated;
                });
                return prev;
            }

            // Indicates whether any bike station is selected
            const stationSet = originIndex >= 0 || destinationIndex >= 0;

            // Converts bicycle segment to multimodal if stations are involved
            const updated: LegPreference[] = prev.map(p => ({
                ...p,
                mode: p.mode === "bicycle" && stationSet ? "multimodal" : p.mode
            }));

            // Assign bicycle mode to all legs between origin and destination stations
            if (originIndex >= 0 && destinationIndex >= 0) {
                for (let i = originIndex; i < destinationIndex; i++) {
                    updated[i].mode = "bicycle";
                }
            }
            // If only origin is set apply bicycle segment after this waypoint
            else if (originIndex >= 0 && originIndex < updated.length) {
                updated[originIndex].mode = "bicycle";
            }
            // If only destination is set apply bicycle segment before this waypoint
            else if (destinationIndex > 0) {
                updated[destinationIndex - 1].mode = "bicycle";
            }

            return updated;
        });
    }, [waypoints]);

    const value = useMemo(() => ({
        waypoints, setWaypoints,
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
        swapWaypoints,
        fieldErrors, setFieldErrors,
        showBikeStations, setShowBikeStations,
        bikeStations
    }), [
        waypoints,
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
        swapWaypoints,
        fieldErrors,
        setPreference,
        setUseOwnBike,
        showBikeStations,
        bikeStations
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
