/**
 * @file MapComponents.tsx
 * @brief Helper functions for map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import L from "leaflet";
import { useMapEvent } from "react-leaflet";
import { PUBLIC_URL } from "../config/config";

/**
 * Creates a custom waypoint marker with a text label
 * 
 * @param label Marker label
 * @param isPreview Indicates whether the waypoint is in preview mode
 * @param translatedLabel Translated label for STAR/END marker
 * @returns Leaflet DivIcon instance
 */
export function createPinIcon(label: string, isPreview: boolean, translatedLabel?: string) {
    // Determine whether the marker represents start or end point
    const startEndMarker = label === "START" || label === "END";
    
    // CSS class applied to the marker 
    const className = "marker " + (startEndMarker ? "start-end-marker " : "") + (isPreview ? "preview-marker" : "");

    // Default anchor positions
    let anchor: [number, number] = [14, 39];
    let popupAnchor: [number, number] = [0, -45];

    // Replace label with translated version for START/END markers
    label = startEndMarker && translatedLabel ? translatedLabel : label;

    // Adjusts anchor positions for START/END markers
    if (startEndMarker) {
        anchor = [20, 53];
        popupAnchor = [0, -55];
    }

    return L.divIcon({
        html: `
            <div class="${className}">
                <div class="marker-inner">${label}</div>
            </div>
        `,
        className: "",
        iconAnchor: anchor,
        popupAnchor: popupAnchor
    });
}

/**
 * Creates a circular marker with a text label for vehicle visualisation
 * 
 * @param label Marker label
 * @param color Background color of the marker based on the route color 
 * @returns Leaflet DivIcon instance
 */
export function createVehiclePositionIcon(label: string, color: string) {
    return L.divIcon({
        html: `
            <div class="vehicle-marker" style="background: ${color};">
                <div class="vehicle-marker-inner">${label}</div>
            </div>
        `,
        className: "",
        iconSize: [22, 22],
        iconAnchor: [11, 11],
        popupAnchor: [0, -11]
    });
}

/**
 * Creates a marker for bicycle station visualisation
 * 
 * @param origin Indicates whether the station is origin, true, or destination, false
 * @returns Leaflet DivIcon instance
 */
export function createBikeStationPin(origin: boolean) {
    // Add class based on the origin parameter
    const typeClass = origin ? "origin-marker" : "destination-marker";

    // Load bicycle station image based on the origin parameter
    const imgSrc = origin ? `${PUBLIC_URL}/img/originStation.svg` : `${PUBLIC_URL}/img/destinationStation.svg`;

    return L.divIcon({
        html: `
            <div class="marker ${typeClass}">
                <div class="marker-inner">
                    <img src="${imgSrc}" class="station-svg" />
                </div>
            </div>
        `,
        className: "",
        iconAnchor: [15, 40],
        popupAnchor: [0, -40],
    });
}

/**
 * Creates a smaller marker for other bicycle stations visualisation
 * 
 * @param origin Indicates whether the station is origin, true, or destination, false
 * @returns Leaflet DivIcon instance
 */
export function createSmallBikeStationPin(origin: boolean) {
    // Add class based on the origin parameter
    const typeClass = origin ? "origin-marker" : "destination-marker";

    return L.divIcon({
        html: `
            <div class="marker small-bike-marker ${typeClass}">
                <div class="marker-inner small-inner"></div>
            </div>
        `,
        className: "",
        iconAnchor: [5, 25],
        popupAnchor: [2, -25],
    });
}

/**
 * Handles map click interaction
 * If the callback returns false the map is moved animated to the clicked position
 * 
 * @param onMapClick Callback handling map click event
 */
export function SetViewOnClick({ onMapClick }: { onMapClick: (lat: number, lng: number) => boolean }) {
    const map = useMapEvent('click', (e) => {
        // Move map to the position
        if (!onMapClick(e.latlng.lat, e.latlng.lng)) {
            map.setView(e.latlng, map.getZoom(), {
                animate: true,
                duration: 0.3
            });
        }
    });
    return null;
}

/** End of file MapComponents.tsx */
