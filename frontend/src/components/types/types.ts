/**
 * @file types.ts
 * @brief Type definitions used in application
 * @author Andrea Svitkova (xsvitka00)
 */

import dayjs from "dayjs";

export type InputText = {
    name: string;
    city: string;
    street: string;
    lat: number;
    lon: number;
};

export type Waypoint = {
    lat: number; 
    lon: number; 
    displayName: string;
    isActive: boolean;
    isPreview: boolean;
    id: any;
};

export type StoredWaypoint = {
    lat: number;
    lon: number;
    name: string;
};

export type Mode = "foot" | "bicycle" | "walk_transit" | "transit,bicycle,walk";

export type LegPreference = {
    mode: Mode;
    wait: dayjs.Dayjs;
    open: boolean;
};

export type Leg = {
    mode: string;
    color: string;
    aimedStartTime: string;
    aimedEndTime: string;
    distance: number;
    duration: number;
    accumulatedDuration: number;
    walkMode?: boolean;
    pointsOnLink: {
        points: string | string[];
    };
    bikeStationInfo?: {
        rack: boolean;
        latitude: number;
        longitude: number;
        origin: boolean;
        selectedBikeStationIndex: number;
        bikeStations: {
            distance: number;
            score: number;
            place: {
                latitude: number;
                longitude: number;
                id: string;
                name: string;
                bikesAvailable: number;
                spacesAvailable: number;
                allowDropoff: boolean;
                capacity?: number;
            };
        }[];
    };
    fromPlace?: {
        latitude?: number;
        longitude?: number;
        name?: string;
        quay?: {
            id: string;
            name: string;
        };
    };
    toPlace?: {
        latitude?: number;
        longitude?: number;
        name?: string;
        quay?: {
            id: string;
            name: string;
        };
    };
    line?: {
        publicCode?: string;
        name?: string;
        id?: string;
    };
    serviceJourney?: {
        direction: string;
        quays: {
            name: string;
        }[];
    };
    otherOptions?: {
        currentIndex: number;
        departures: {
            departureTime: string;
            direction: string;
        }[];
    };
    delays?: {[date: string]: number};
    nonContinuousDepartures?: boolean;
    arrivalAfterDeparture?: boolean;
};

export type RoutePreference = "shortest" | "fastest" | "transfers";

export type VehiclePosition = {
    tripId: number;
    publicCode: string;
    mode: string;
    color: string;
    lat: number;
    lon: number;
    direction: string;
};

export type TripPattern = {
    aimedEndTime: string;
    totalDuration: number;
    totalDistance: number;
    numOfTransfers?: number;
    legs: Leg[];
    originalLegs: Leg[];
    modes: string[];
    polyInfo: PolyInfo[];
    bounds?: L.LatLngBounds;
    tooLongWalkDistance?: boolean;
    tooLongBikeDistance?: boolean;
    vehiclePositions: VehiclePosition[];
};

export type ResultsType = {
    tripPatterns: TripPattern[];
    active: boolean;
};

export type PolyInfo = {
    coords: [number, number][];
    mode: string;
    color: string;
    pathOptions: {"dashArray"?: string};
};

export type VerticalTimeline = {
    mode: string;
    length: number;
    color: string;
};

/** End of file types.ts */
