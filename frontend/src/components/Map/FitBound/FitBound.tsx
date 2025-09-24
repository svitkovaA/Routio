/**
 * @file FitBound.tsx
 * @brief Adjusts map view to fit the bounds of the selected trip pattern
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useMemo } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import { ResultsType } from "../../types/types";

type FitBoundProps = {
    sidebarOpen: boolean;
    results: ResultsType[];
    resultActiveIndex: number;
    selectedTripPatternIndex: number;
}

function FitBound({ 
    sidebarOpen,
    results,
    resultActiveIndex,
    selectedTripPatternIndex
}: FitBoundProps) {
    const map = useMap();

    const bounds = useMemo(() => {
        if (resultActiveIndex === -1 || !results[resultActiveIndex].active || !results[resultActiveIndex].tripPatterns[selectedTripPatternIndex]?.legs) {
            return null;
        }
        const tripPattern = results[resultActiveIndex].tripPatterns[selectedTripPatternIndex]

        if (tripPattern?.southWest && tripPattern?.northWest) {
            return L.latLngBounds(tripPattern.southWest, tripPattern.northWest);
        }

        const polyInfo = tripPattern.polyInfo;

        if (polyInfo.length === 0) {
            return null;
        }
        
        const firstCoords = polyInfo.find(p => p.coords.length > 0)?.coords;
        if (!firstCoords) {
            return null;
        }

        let minLat = firstCoords[0][0];
        let maxLat = firstCoords[0][0];
        let minLon = firstCoords[0][1];
        let maxLon = firstCoords[0][1];
    
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
    }, [results, resultActiveIndex, selectedTripPatternIndex]);

    useEffect(() => {
        if (!bounds) return;

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
