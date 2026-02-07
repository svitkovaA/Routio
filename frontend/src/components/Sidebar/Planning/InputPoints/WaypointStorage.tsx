import { StoredWaypoint, Waypoint } from "../../../types/types";

const MAX_STORED_WAYPOINTS = 5;
const MIDDLE_WAYPOINTS = "middle_waypoints";
const ORIGIN = "first_waypoints";
const DESTINATION = "last_waypoints";

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
    const seen = new Set<string>();

    for (const waypoint of merged) {
        const key = `${waypoint.lat},${waypoint.lon}`;
        if (!seen.has(key)) {
            seen.add(key);
            unique.push(waypoint);
        }
    }

    save(MIDDLE_WAYPOINTS, unique.slice(0, MAX_STORED_WAYPOINTS));
}

function storeWaypoint(waypoint: StoredWaypoint, key: string) {
    const stack = load(key);

    for (let i = 0; i < stack.length; i++) {
        if (stack[i].lat === waypoint.lat && stack[i].lon === waypoint.lon) {
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
