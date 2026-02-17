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
    sidebarOpen: boolean;   // Indicates whether the sidebar is currently open
}

function FitBound({ 
    sidebarOpen
}: FitBoundProps) {
    // Result context
    const { pattern, mobileSidebarHeight } = useResult();

    // Leaflet map instance
    const map = useMap();

    // Computes map bounds for the active trip pattern
    const bounds = useMemo(() => {
        // No route polyline data available
        if (!pattern?.polyInfo?.length) {
            return null;
        }

        const polyInfo = pattern.polyInfo;
        
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
    }, [pattern?.polyInfo]);

    /**
     * Updates the map view whenever computed bounds or sidebar state changes.
     */
    useEffect(() => {
        if (!bounds) return;

        // Detect mobile layout
        const isMobile = window.innerWidth < 768;

        // Adjust mobile layout for route to fit map bounds
        if (isMobile) {
            map.fitBounds(bounds, {
                paddingTopLeft: [50, 50],
                paddingBottomRight: [50, mobileSidebarHeight + 50],
            });
        }
        // Adjust notebook layout with open sidebar for route to fit map bounds
        else if (sidebarOpen) {
            map.fitBounds(bounds, {
                paddingTopLeft: [370, 50],
                paddingBottomRight: [50, 50],
            });
        }
        // Adjust notebook layout with closed sidebar for route to fit map bounds
        else {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [bounds, mobileSidebarHeight, map, sidebarOpen]);

    return null;
}

export default FitBound;

/** End of file FitBound.tsx */
