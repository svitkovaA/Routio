/**
 * @file FitBound.tsx
 * @brief Adjusts the map view to fit the bounds of the selected trip pattern
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useMemo } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import { useResult } from "../../ResultContext";

type FitBoundProps = {
    sidebarOpen: boolean;   // State indicating whether the sidebar is currently open
}

function FitBound({ sidebarOpen }: FitBoundProps) {
    // Result context
    const {
        resultActiveIndex,
        result,
        pattern
    } = useResult();

    // Leaflet map instance
    const map = useMap();

    // Computes map bounds for the active trip pattern
    const bounds = useMemo(() => {
        if (resultActiveIndex === -1 || !result.active || !pattern?.legs) {
            return null;
        }

        // Use precomputed bounds if available
        if (pattern?.southWest && pattern?.northWest) {
            return L.latLngBounds(pattern.southWest, pattern.northWest);
        }

        const polyInfo = pattern.polyInfo;

        if (polyInfo.length === 0) {
            return null;
        }
        
        // Initialize bounds using first available coordinate
        const firstCoords = polyInfo.find(p => p.coords.length > 0)?.coords;
        if (!firstCoords) {
            return null;
        }

        let minLat = firstCoords[0][0];
        let maxLat = firstCoords[0][0];
        let minLon = firstCoords[0][1];
        let maxLon = firstCoords[0][1];
    
        // Compute bounding box from all polyline coordinates
        for (let i = 0; i < polyInfo.length; i++) {
            for (let j = 0; j < polyInfo[i].coords.length; j++) {

                if (polyInfo[i].coords[j][0] < minLat) {
                    minLat = polyInfo[i].coords[j][0];
                }
                if (polyInfo[i].coords[j][0] > maxLat) {
                    maxLat = polyInfo[i].coords[j][0];
                }
                if (polyInfo[i].coords[j][1] < minLon) {
                    minLon = polyInfo[i].coords[j][1];
                }
                if (polyInfo[i].coords[j][1] > maxLon) {
                    maxLon = polyInfo[i].coords[j][1];
                }
            }
        }
        return L.latLngBounds(L.latLng(minLat, minLon), L.latLng(maxLat, maxLon));
    }, [resultActiveIndex, pattern, result.active]);

    /**
     * Updates the map view whenever computed bounds or sidebar state changes.
     */
    useEffect(() => {
        if (!bounds) return;

        // Adjust padding to account for sidebar on larger screens
        if (sidebarOpen && window.innerWidth > 768) {
            map.fitBounds(bounds, {
                paddingTopLeft: [370, 50],
                paddingBottomRight: [50, 50],
            });
        } 
        else {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [bounds, sidebarOpen, map]);

    return null;
}

export default FitBound;

/** End of file FitBound.tsx */
