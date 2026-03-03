/**
 * @file ShowRoute.tsx
 * @brief Renders map routes polylines on the map based on trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { Polyline } from "react-leaflet";
import polyline from '@mapbox/polyline';
import { useResult } from "../../ResultContext";

function ShowRoute() {
    // Result context
    const {
        resultActiveIndex, 
        results,
        selectedTripPatternIndex,
        showResults, setResults,
        result,
        pattern
    } = useResult();

    // State for force rerender after polyline computation
    const [forceUpdate, setForceUpdate] = useState(0);
    
    /**
     * Computes and stores decoded polyline data for the active trip pattern
     */
    useEffect(() => {
        // Validate required state
        if (resultActiveIndex === -1 || !result?.active || !pattern?.legs) {
            return;
        }
        
        // Do not recompute if polyline data already exists
        if (pattern.polyInfo.length !== 0) {
            return;
        }
        
        const legs = pattern.legs;

        // Decode polyline coordinates for each leg
        const polyInfoTemp = legs.map(leg => {
            const coords = Array.isArray(leg.pointsOnLink.points) ? leg.pointsOnLink.points.flatMap(p => polyline.decode(p)) : polyline.decode(leg.pointsOnLink.points);
            const inactiveCoords = leg.pointsOnLink.inactivePoints.map(p => polyline.decode(p));
            
            return {
                coords: coords,
                inactiveCoords: inactiveCoords,
                mode: leg.mode || 'unknown',
                color: leg.color || '#000000',
                pathOptions: leg.mode === "foot" || leg.mode === "bicycle" ? {dashArray: "5px, 5px"} : {}
            };
        });
        
        // Store computed polyline information in results context
        const newResults = [...results];
        newResults[resultActiveIndex].tripPatterns[selectedTripPatternIndex].polyInfo = polyInfoTemp;
        setResults(newResults);
        
        // Force rerender to update displayed polylines
        setForceUpdate(prev => prev + 1);
    }, [results, resultActiveIndex, selectedTripPatternIndex, pattern, setResults, result?.active]);
    
    // Do not render if results are not available
    if (!showResults || 
        resultActiveIndex === -1 || 
        !result?.active || 
        !pattern?.legs) {
        return null;
    }
    
    const polyInfo = pattern.polyInfo || [];
    
    // Do not render if no polyline data is available
    if (polyInfo.length === 0) {
        return null;
    }
    
    return (
        <>
            {polyInfo.map((info, index) => (
                <>
                    <Polyline
                        key={`outline-${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${forceUpdate}`}
                        positions={info.coords}
                        color="rgba(255,255,255,0.7)"
                        pathOptions={{
                            ...info.pathOptions,
                            weight: info.pathOptions?.dashArray === "5px, 5px" ? 2 : 6
                        }}
                    />
                    <Polyline
                        key={`main-${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${forceUpdate}`}
                        positions={info.coords}
                        color={info.color}
                        pathOptions={{
                            ...info.pathOptions,
                            weight: 4
                        }}
                    />
                    {info.inactiveCoords.map((c, i) => (
                         <Polyline
                            key={`${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${forceUpdate}-inactive-${i}`}
                            positions={c}
                            color={info.color}
                            pathOptions={{
                                ...info.pathOptions,
                                opacity: 0.6,
                                weight: 2,
                            }}
                        />
                    ))}
                </>
            ))}
        </>
    );
}

export default ShowRoute;

/** End of file ShowRoute.tsx */
