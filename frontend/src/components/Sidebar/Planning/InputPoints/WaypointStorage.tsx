/**
 * @file WaypointStorage.tsx
 * @brief Utility for loading and storing waypoints to local storage
 * @author Andrea Svitkova (xsvitka00)
 */

import { StoredWaypoint, Waypoint } from "../../../types/types";

// Maximum number of stored waypoints per category (origin, middle stops, destination)
const MAX_STORED_WAYPOINTS = 5;

// Local storage keys
const MIDDLE_WAYPOINTS = "middle_waypoints";
const ORIGIN = "first_waypoints";
const DESTINATION = "last_waypoints";

// Maximum distance for considering to waypoints the same
const MAX_DISTANCE = 100;

/**
 * Calculates distance between two coordinates using Haversine formula
 * 
 * @param lat1 Latitude coordinate of the first waypoint
 * @param lon1 Longitude coordinate of the first waypoint
 * @param lat2 Latitude coordinate of the second waypoint
 * @param lon2 Longitude coordinate of the second waypoint
 * @returns Distance between two waypoints in meters
 */
function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    // Earth radius
    const R = 6371000;

    // Converts degrees to radians
    const toRad = (deg: number) => (deg * Math.PI) / 180;

    // Differences in latitude and longitude
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);

    // Application of Haversine formula
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
}

/**
 * Determines whether two stored waypoints represent the same location
 * 
 * @param waypoint1 First waypoint to checked
 * @param waypoint2 Second waypoint to checked
 * @returns True if the waypoints are considered same, false otherwise
 */
function isSameWaypoint(waypoint1: StoredWaypoint, waypoint2: StoredWaypoint): boolean {
    // Check names
    if (waypoint1.name !== waypoint2.name) {
        return false;
    }

    // Check the distance between two points with the same name
    const distance = haversineDistance(waypoint1.lat, waypoint1.lon, waypoint2.lat, waypoint2.lon);

    return distance < MAX_DISTANCE;
}

/**
 * Loads stored waypoint array from local storage
 * 
 * @param key Key to local storage
 * @returns Parsed waypoint array or empty array
 */
function load(key: string): StoredWaypoint[] {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
}

/**
 * Saves waypoint array into local storage
 * 
 * @param key Key to local storage
 * @param data The data to be stored to local storage
 */
function save(key: string, data: StoredWaypoint[]) {
    localStorage.setItem(key, JSON.stringify(data));
}

/**
 * Stores intermediate waypoints
 * 
 * @param waypoints Intermediate waypoints
 * @param yourLocation String representing the detected location
 */
function storeMiddleWaypoints(waypoints: StoredWaypoint[], yourLocation: string) {
    // Do not store empty input
    if (waypoints.length === 0) {
        return;
    }

    // Load stored middle waypoints
    const stored = load(MIDDLE_WAYPOINTS);
    // Merge new waypoints with stored one
    const merged = [...waypoints, ...stored];

    const unique: StoredWaypoint[] = [];

    // Remove duplicities
    for (const waypoint of merged) {
        // Skip your location
        if (waypoint.name === yourLocation) {
            continue;
        }

        const exists = unique.some((u) => isSameWaypoint(u, waypoint));
        
        if (!exists) {
            unique.push(waypoint);
        }
    }

    // Store most recent waypoints
    save(MIDDLE_WAYPOINTS, unique.slice(0, MAX_STORED_WAYPOINTS));
}

/**
 * Stores single waypoint
 * 
 * @param waypoint The waypoint to be stored
 * @param key Key to local storage
 * @param yourLocation String representing the detected location
 */
function storeWaypoint(waypoint: StoredWaypoint, key: string, yourLocation: string) {
    // Skip your location
    if (waypoint.name === yourLocation) {
        return;
    }

    // Load stored stack
    const stack = load(key);

    // Remove duplicities
    for (let i = 0; i < stack.length; i++) {
        if (isSameWaypoint(stack[i], waypoint)) {
            stack.splice(i, 1);
            break;
        }
    }

    // Insert new waypoint at the beginning and save
    stack.unshift(waypoint);
    save(key, stack.slice(0, MAX_STORED_WAYPOINTS));
}

/**
 * Stores route waypoints 
 * 
 * @param waypoints Waypoints to be stored
 * @param yourLocation String representing the detected location
 */
export const storeWaypoints = (waypoints: Waypoint[], yourLocation: string) => {    
    let waypointsToStore: StoredWaypoint[] = [];

    // Convert Waypoint to StoredWaypoint format
    for (let i = 0; i < waypoints.length; i++) {
        waypointsToStore.push({
            lat: waypoints[i].lat,
            lon: waypoints[i].lon,
            name: waypoints[i].displayName
        });
    }

    // Store origin
    storeWaypoint(waypointsToStore[0], ORIGIN, yourLocation);

    // Store destination
    storeWaypoint(waypointsToStore[waypointsToStore.length - 1], DESTINATION, yourLocation);
    
    // Store intermediate waypoints
    storeMiddleWaypoints(waypointsToStore.slice(1, -1), yourLocation);
};

/**
 * Loads stored origin waypoints
 */
export const loadOrigin = () => {
    return load(ORIGIN);
};

/**
 * Loads stored intermediate waypoints
 */
export const loadMiddleWaypoints = () => {
    return load(MIDDLE_WAYPOINTS);
};

/**
 * Loads stored destination waypoints
 */
export const loadDestination = () => {
    return load(DESTINATION);
};

/** End of file WaypointStorage.tsx */
