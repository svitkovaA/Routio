/**
 * @file ShowRoute.tsx
 * @brief Renders map routes based on trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { Polyline } from "react-leaflet";
import polyline from '@mapbox/polyline';
import { useResult } from "../../ResultContext";

function ShowRoute() {
    const {
        resultActiveIndex, 
        results,
        selectedTripPatternIndex,
        showResults, setResults,
        result,
        pattern
    } = useResult();

    const [forceUpdate, setForceUpdate] = useState(0);
    
    useEffect(() => {
        if (resultActiveIndex === -1 || !result?.active || !pattern?.legs) {
            return;
        }
        
        const legs = pattern.legs;
        if (pattern.polyInfo.length !== 0) {
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
        !result?.active || 
        !pattern?.legs) {
        return null;
    }
    
    const polyInfo = pattern.polyInfo || [];
    
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
