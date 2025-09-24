/**
 * @file ShowRoute.tsx
 * @brief Renders map routes based on trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { Polyline } from "react-leaflet";
import polyline from '@mapbox/polyline';
import { ResultsType } from "../../types/types";

type ShowRouteProps = {
    results: ResultsType[];
    setResults: (value: ResultsType[]) => void;
    showResults: boolean;
    resultActiveIndex: number;
    selectedTripPatternIndex: number;
};

function ShowRoute({
    results,
    setResults,
    showResults,
    resultActiveIndex,
    selectedTripPatternIndex
} : ShowRouteProps) {  
    const [forceUpdate, setForceUpdate] = useState(0);
    
    useEffect(() => {
        if (resultActiveIndex === -1 || !results[resultActiveIndex]?.active || !results[resultActiveIndex].tripPatterns[selectedTripPatternIndex]?.legs) {
            return;
        }
        
        const currentTripPattern = results[resultActiveIndex].tripPatterns[selectedTripPatternIndex];
        const legs = currentTripPattern.legs;
        if (currentTripPattern.polyInfo.length !== 0) {
            return;
        }
            
        const polyInfoTemp = legs.map(leg => {
            const coords = Array.isArray(leg.pointsOnLink.points) ? leg.pointsOnLink.points.flatMap(p => polyline.decode(p)) : polyline.decode(leg.pointsOnLink.points);
            
            return {
                coords: coords,
                mode: leg.mode || 'unknown',
                color: leg.color || '#000000',
                pathOptions: leg.mode === "foot" || leg.mode === "bicycle" ? {dashArray: "5px, 5px"} : {}
            };
        });
        
        const newResults = [...results];
        newResults[resultActiveIndex].tripPatterns[selectedTripPatternIndex].polyInfo = polyInfoTemp;
        setResults(newResults);
        
        setForceUpdate(prev => prev + 1);
    }, [results, resultActiveIndex, selectedTripPatternIndex]);
    
    if (!showResults || 
        resultActiveIndex === -1 || 
        !results[resultActiveIndex]?.active || 
        !results[resultActiveIndex].tripPatterns[selectedTripPatternIndex]?.legs) {
        return null;
    }
    
    const polyInfo = results[resultActiveIndex].tripPatterns[selectedTripPatternIndex].polyInfo || [];
    
    if (polyInfo.length === 0) {
        return null;
    }
    
    return (
        <>
            {polyInfo.map((info, index) => (
                <Polyline
                    key={`${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${forceUpdate}`}
                    positions={info.coords}
                    color={info.color}
                    pathOptions={info.pathOptions}
                />
            ))}
        </>
    );
}

export default ShowRoute;

/** End of file ShowRoute.tsx */
