import { StoredWaypoint, Waypoint } from "../../../types/types";

const MAX_STORED_WAYPOINTS = 5;
const MIDDLE_WAYPOINTS = "middle_waypoints";
const ORIGIN = "first_waypoints";
const DESTINATION = "last_waypoints";
// The distance for which the locations are considered the same
const MAX_DISTANCE = 100;

function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371000;
    const toRad = (deg: number) => (deg * Math.PI) / 180;

    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    // Distance between two points in meters
    return R * c;
}

function isSameWaypoint(a: StoredWaypoint, b: StoredWaypoint): boolean {
    // Check names
    if (a.name !== b.name) {
        return false;
    }

    // Check the distance between two points with the same name
    const distance = haversineDistance(a.lat, a.lon, b.lat, b.lon);
    return distance < MAX_DISTANCE;
}

function load(key: string): StoredWaypoint[] {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
}

function save(key: string, data: StoredWaypoint[]) {
    localStorage.setItem(key, JSON.stringify(data));
}

function storeMiddleWaypoints(waypoints: StoredWaypoint[]) {
    if (waypoints.length === 0) {
        return;
    }

    const stored = load(MIDDLE_WAYPOINTS);
    const merged = [...waypoints, ...stored];

    const unique: StoredWaypoint[] = [];

    for (const waypoint of merged) {
        const exists = unique.some((u) => isSameWaypoint(u, waypoint));
        if (!exists) {
            unique.push(waypoint);
        }
    }

    save(MIDDLE_WAYPOINTS, unique.slice(0, MAX_STORED_WAYPOINTS));
}

function storeWaypoint(waypoint: StoredWaypoint, key: string) {
    const stack = load(key);

    for (let i = 0; i < stack.length; i++) {
        if (isSameWaypoint(stack[i], waypoint)) {
            stack.splice(i, 1);
            break;
        }
    }

    stack.unshift(waypoint);
    save(key, stack.slice(0, MAX_STORED_WAYPOINTS));
}

export const storeWaypoints = (waypoints: Waypoint[]) => {
    let waypointsToStore: StoredWaypoint[] = [];
    for (let i = 0; i < waypoints.length; i++) {
        waypointsToStore.push({
            lat: waypoints[i].lat,
            lon: waypoints[i].lon,
            name: waypoints[i].displayName
        });
    }

    storeWaypoint(waypointsToStore[0], ORIGIN);
    storeWaypoint(waypointsToStore[waypointsToStore.length - 1], DESTINATION);
    storeMiddleWaypoints(waypointsToStore.slice(1, -1));
};

export const loadOrigin = () => {
    return load(ORIGIN);
};

export const loadMiddleWaypoints = () => {
    return load(MIDDLE_WAYPOINTS);
};

export const loadDestination = () => {
    return load(DESTINATION);
};
