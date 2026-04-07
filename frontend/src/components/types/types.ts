/**
 * @file types.ts
 * @brief Type definitions used in application
 * @author Andrea Svitkova (xsvitka00)
 */

import dayjs from "dayjs";
import L from 'leaflet';

/**
 * Represents structured location
 */
export type InputText = {
    name: string;                           // Place name
    city: string;                           // City name
    street: string;                         // Street name
    lat: number;                            // Location latitude coordinate
    lon: number;                            // Location longitude coordinate
};

/**
 * Represents shared bicycle station
 */
export type Station = {
    id: string;                             // Station id
    lat: number;                            // Station latitude
    lon: number;                            // Station longitude
    name: string;                           // Station name
}

/**
 * Represents a waypoint used during route planning.
 * Can be origin, destination or intermediate point
 */
export type Waypoint = {
    lat: number;                            // Latitude coordinate
    lon: number;                            // Longitude coordinate
    displayName: string;                    // Name displayed on UI
    isActive: boolean;                      // Indicates whether the waypoint is currently selected
    isPreview: boolean;                     // Indicates whether the waypoint is shown only as a preview 
    id: string;                             // Internal identifier
    bikeStationId: string | null;           // Station identifier
    origin: boolean | null;                 // True if station is set as origin one, false otherwise
};

/**
 * Simplified waypoint structure used for storing into local storage
 */
export type StoredWaypoint = {
    lat: number;                            // Latitude coordinate
    lon: number;                            // Longitude coordinate
    name: string;                           // Stored display name
};

/**
 * Supported transportation modes
 */
export type Mode = "foot" | "bicycle" | "walk_transit" | "multimodal";

/**
 * Represents user preference configuration for single leg
 */
export type LegPreference = {
    mode: Mode;                             // Selected transportation mode
    wait: dayjs.Dayjs;                      // Selected wait time in the stop 
    open: boolean;                          // Indicates whether preference panel for leg is expanded in UI
    fixed: boolean;                         // Indicates whether mode is fixes and cannot be changed
};

/**
 * Represents alternative bike station with metadata
 */
export type BikeStation = {
    distance: number;               // Distance from waypoint/relevant point to the bike station
    score: number;                  // Computed score used for ranking stations
    place: {
        latitude: number;           // Latitude coordinate
        longitude: number;          // Longitude coordinate
        id: string;                 // Internal station identifier
        name: string;               // Bike station name
        bikesAvailable: number;     // Number of currently available bikes
        predictedBikes?: number;    // Number of predicted bikes in station
        capacity?: number;          // Total station capacity
    };
};

/**
 * Represents one leg segment of a trip pattern
 */
export type Leg = {
    mode: string;                           // Transport mode used on the leg segment
    color: string;                          // Color used for visualisation of the leg on map
    aimedStartTime: string;                 // Aimed departure time in ISO string format
    aimedEndTime: string;                   // Aimed arrival time in ISO string format
    distance: number;                       // Distance of this leg in meters
    duration: number;                       // Duration of this leg in seconds
    accumulatedDuration: number;            // Accumulated duration from beginning of the trip up to this leg segment in seconds
    walkMode?: boolean;                     // Indicates whether the leg represents an explicit walking segment
    pointsOnLink: {
        points: string | string[];          // Encoded polyline or list of polylines representing the geometry of this leg
        inactivePoints: string[];           // Encoded polylines representing an inactive route segments
    };
    tripId?: string;                        // GTFS trip identifier
    delay?: number;                         // Real time vehicle delay
    zone_ids?: number[];                    // List of faze zone identifiers

    /**
     * Information about related bike stations, present only in bike related legs
     */
    bikeStationInfo?: {
        rack: boolean;                      // Indicates whether this station is a rack (for own bicycle)
        latitude: number;                   // Latitude coordinate
        longitude: number;                  // Longitude coordinate
        origin: boolean;                    // Indicates whether this station is origin one, or destination, false
        selectedBikeStationIndex: number;   // Index of the currently selected bike station in the list

        /** List of alternative bike stations with metadata */
        bikeStations: BikeStation[];
    };

    /**
     * Information about the departure place of this leg
     */
    fromPlace?: {
        latitude?: number;                  // Latitude coordinate
        longitude?: number;                 // Longitude coordinate
        name?: string;                      // Departure place name
        quay?: {
            id: string;                     // Quay, stop information identifier
            name: string;                   // Quay, stop name
        };
    };

    /**
     * Information about the arrival place of this leg
     */
    toPlace?: {
        latitude?: number;                  // Latitude coordinate
        longitude?: number;                 // Longitude coordinate
        name?: string;                      // Arrival place name
        quay?: {
            id: string;                     // Quay, stop information identifier
            name: string;                   // Quay, stop name
        };
    };

    /**
     * Public transport line information
     */
    line?: {
        publicCode?: string;                // Public transport line number
        name?: string;                      // Full line name
        id?: string;                        // Internal line identifier
    };

    /**
     * Service journey information for public transport
     */
    serviceJourney?: {
        direction: string;                  // Direction name, final route stop
        quays: {
            name: string;                   // Ordered list of quays, stops, served by this journey
        }[];
        startOffset?: number;               // Stop start index
        currentIndex: number | null;        // Current vehicle stop index
    };

    /**
     * Alternative departure options for this leg
     */
    otherOptions?: {
        currentIndex: number;               // Index of currently selected departure option
        departures: {
            departureTime: string;          // List of alternative departure times
            direction: string;              // List of alternative directions
        }[];
    };

    delays?: {[date: string]: number};      // Historical delay information
    nonContinuousDepartures?: boolean;      // Indicates that there are no further continuous departures available
    arrivalAfterDeparture?: boolean;        // Indicates data inconsistency where arrival time is after departure time
    artificial: boolean;                    // Indicates artificial leg
};

/**
 * Defines available route optimization preferences
 */
export type RoutePreference = "shortest" | "fastest" | "transfers";

/**
 * Represents real-time vehicle position data
 */
export type VehiclePosition = {
    agencyName: string;                     // GTFS agency name
    tripId: string;                         // Internal trip identifier
    publicCode: string;                     // Public line code
    mode: string;                           // Transport mode
    color: string;                          // Display color associated with the line
    lat: number;                            // Current latitude of the vehicle
    lon: number;                            // Current longitude of the vehicle
    delay?: number;                         // Current vehicle delay
    direction: string;                      // Direction of the vehicle, final stop name
    startTime: string;                      // Vehicle journey start time
    stopIndex?: number;                     // Index of the closes stop
};

/**
 * Represents one complete trip pattern
 */
export type TripPattern = {
    aimedEndTime: string;                   // Planned arrival time of the whole trip in ISO string format
    totalDuration: number;                  // Total travel duration in seconds
    totalDistance: number;                  // Total travel distance in meters
    totalTime: number;                      // Total trip time from start to the end
    numOfTransfers?: number;                // Total number of transfers
    legs: Leg[];                            // Processed legs
    originalLegs: Leg[];                    // Original legs, non processed legs
    modes: string[];                        // List of transport modes used in this trip pattern
    bounds?: L.LatLngBounds;                // Geographical bounds of the trip used to fit map view
    tooLongWalkDistance?: boolean;          // Indicates that walking distance exceeds threshold defined by user
    tooLongBikeDistance?: boolean;          // Indicates that cycling distance exceeds threshold defined by user
    vehicleRealtimeData: VehiclePosition[]; // Real-time positions of vehicles associated with this trip
};

/**
 * Represents the complete result object
 */
export type ResultsType = {
    tripPatterns: TripPattern[];            // List of available trip alternatives
    active: boolean;                        // Indicates whether results are currently displayed
};

/**
 * Represents a single sampled point in an elevation profile
 */
export type ElevationPoint = {
    lat: number;                            // Latitude of the sampled point
    lon: number;                            // Longitude of the sampled point
    elevation: number;                      // Elevation at this point in meters above sea level
    distance: number;                       // Distance from the start of the route in meters
};

/**
 * Represents rendering information for a leg polyline
 */
export type PolyInfo = {
    coords: [number, number][];             // Ordered list of coordinates [latitude, longitude]
    inactiveCoords: [number, number][][];
    mode: string;                           // Transport mode associated with this polyline segment
    color: string;                          // Color used for rendering the polyline
    pathOptions: {
        "dashArray"?: string                // Additional Leaflet path styling options
    };
    tripId?: string;                        // Trip identifier
    elevationProfile?: ElevationPoint[];    // Computed elevation profile for this leg (foot, bicycle only)
    totalAscent?: number;                   // Total elevation gain in meters for the leg
    totalDescent?: number;                  // Total elevation loss in meters for the leg
    elevationOpen: boolean;                 // Flag indicating whether the elevation profile for this leg is visible
};

/**
 * Represents a simplified segment used in the vertical timeline visualization
 */
export type VerticalTimeline = {
    mode: string;                           // Transport mode of the timeline segment
    length: number;                         // Length of the segment
    color: string;                          // Color associated with the segment
    artificial: boolean;                    // Indicates artificial leg
};

/** End of file types.ts */
