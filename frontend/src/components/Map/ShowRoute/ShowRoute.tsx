/**
 * @file ShowRoute.tsx
 * @brief Renders map routes polylines on the map based on trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useMemo } from "react";
import { Polyline, useMap } from "react-leaflet";
import { useResult } from "../../Contexts/ResultContext";
import React from "react";
import { CircleMarker } from "react-leaflet";
import { useMapEvents } from "react-leaflet";

function ShowRoute() {
    // Result context
    const {
        resultActiveIndex, 
        selectedTripPatternIndex,
        showResults,
        vehicleRealtimeData,
        polyInfo,
        polylineForceUpdate,
        hoveredProfileIndex,
        elevationLegIndex,
        setElevationLegIndex,
        setHoveredProfileIndex,
        showBikeStations,
        pattern
    } = useResult();

    /**
     * Creates a map tripId -> vehicle realtime data
     */
    const vehicleMap = useMemo(() => {
        const map = new Map();
        vehicleRealtimeData.forEach(v => {
            map.set(v.tripId, v);
        });
        return map;
    }, [vehicleRealtimeData]);

    // Determines whether bike stations are closed
    const stationsClosed = showBikeStations.every(s => !s);

    const map = useMap();
    const zoom = map.getZoom();

    // Pixel distance threshold for detecting nearest elevation point
    let hoverThresholdPx = 30;

    if (zoom <= 9) hoverThresholdPx = 30;
    else if (zoom === 10) hoverThresholdPx = 24;
    else if (zoom === 11) hoverThresholdPx = 18;
    else if (zoom === 12) hoverThresholdPx = 12;
    else if (zoom <= 14) hoverThresholdPx = 10;
    else if (zoom <=18) hoverThresholdPx = 45;
    else hoverThresholdPx = 10;

    useEffect(() => {
        if (!map.getPane("markerTopPane")) {
            const pane = map.createPane("markerTopPane");
            pane.style.zIndex = "610";
        }
    }, [map]);

    useMapEvents({
        mousemove(e) {
            // Disable elevation hover when bike stations are visible
            if (!stationsClosed) {
                return;
            }

            let bestLeg = null;
            let bestIndex = 0;
            let bestDist = Infinity;

            // Convert mouse position to pixel coordinates
            const mousePoint = map.latLngToLayerPoint(e.latlng);

            // Iterate through all route legs and their elevation points to find
            // the closest point to the cursor
            polyInfo.forEach((leg, legIndex) => {
                if (!leg.elevationProfile) {
                    return;
                }

                leg.elevationProfile.forEach((p, pointIndex) => {
                    // Converts coordinates from geographic coordinates to pixels
                    const point = map.latLngToLayerPoint([p.lat, p.lon]);

                    // Computes distance between  a mouse cursor and the elevation point
                    const dx = point.x - mousePoint.x;
                    const dy = point.y - mousePoint.y;

                    const d = dx * dx + dy * dy;

                    if (d < bestDist) {
                        bestDist = d;
                        bestIndex = pointIndex;
                        bestLeg = legIndex;
                    }

                });

            });

            // Update hovered elevation point if it is within threshold distance
            if (bestLeg !== null && bestDist < hoverThresholdPx * hoverThresholdPx) {
                setElevationLegIndex(bestLeg);
                setHoveredProfileIndex(bestIndex);
            } 
            else {
                setElevationLegIndex(null);
                setHoveredProfileIndex(null);
            }
        }
    });

    useEffect(() => {
        if (!map.getPane("routeInactivePane")) {
            const pane = map.createPane("routeInactivePane");
            pane.style.zIndex = "200";
        }

        if (!map.getPane("routeActivePane")) {
            const pane = map.createPane("routeActivePane");
            pane.style.zIndex = "400";
        }
    }, [map]);

    
    // Do not render if there are no results
    if (!showResults || polyInfo.length === 0) {
        return null;
    }

    let elevationLeg = null;
    let markerPosition = null;

    // Determine marker position for hovered elevation point
    if (elevationLegIndex !== null && stationsClosed) {
        elevationLeg = polyInfo[elevationLegIndex] ?? null;
        
        if (
            hoveredProfileIndex !== null &&
            elevationLeg?.elevationProfile &&
            hoveredProfileIndex < elevationLeg.elevationProfile.length &&
            elevationLeg.elevationOpen
        ) {
            markerPosition = hoveredProfileIndex !== null &&
                elevationLeg?.elevationProfile &&
                elevationLeg.elevationProfile[hoveredProfileIndex]
                    ? [
                        elevationLeg.elevationProfile[hoveredProfileIndex].lat,
                        elevationLeg.elevationProfile[hoveredProfileIndex].lon
                    ]
                    : null;
        }
    }

    return (
        <React.Fragment key={`${resultActiveIndex}-${selectedTripPatternIndex}-${polylineForceUpdate}`}>
            {/* Render route polylines for each leg of the trip */}
            {polyInfo.map((info, index) => {
                const vehiclePosition = vehicleMap.get(info.tripId);

                // Determines whether realtime vehicle data are present and the inactive coordinates will be displayed
                const displayInactiveCoords = vehiclePosition !== undefined && vehiclePosition.lat !== -1 && vehiclePosition.lon !== -1;
                
                return (
                    <React.Fragment key={`route-${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${polylineForceUpdate}`} >
                        {/* Render inactive route segments when realtime vehicle position is available */}
                        {displayInactiveCoords && info.inactiveCoords.map((c, i) => (
                            <Polyline
                                pane="routeInactivePane"
                                key={`${resultActiveIndex}-${selectedTripPatternIndex}-${index}-inactive-${i}-${polylineForceUpdate}`}
                                positions={c}
                                color={info.color}
                                pathOptions={{
                                    ...info.pathOptions,
                                    opacity: 0.6,
                                    weight: 2,
                                }}
                            />
                        ))}

                        {/* White outline polyline for active coordinates */}
                        <Polyline
                            pane="routeActivePane"
                            key={`outline-${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${polylineForceUpdate}-${info.color}`}
                            positions={info.coords}
                            color={"rgba(255,255,255,0.7)"}
                            pathOptions={{
                                ...info.pathOptions,
                                weight: info.pathOptions?.dashArray === "5px, 5px" ? 2 : 6
                            }}
                        />
                        {/* Main polyline for active coordinates */}
                        <Polyline
                            pane="routeActivePane"
                            key={`main-${resultActiveIndex}-${selectedTripPatternIndex}-${index}-${polylineForceUpdate}-${info.color}`}
                            positions={info.coords}
                            color={info.color}
                            pathOptions={{
                                ...info.pathOptions,
                                weight: 4
                            }}
                        />
                    </React.Fragment>
                );
            })}

            {/* Marker showing the hovered elevation point on the map */}
            {markerPosition && (
                <CircleMarker
                    pane="markerTopPane"
                    center={markerPosition as [number, number]}
                    radius={6}
                    pathOptions={{ color: "var(--color-info)", fillColor: "white", fillOpacity: 1 }}
                />
            )}

            {/* Markers for transfers */}
            {pattern && pattern?.originalLegs.filter(l => l.mode === "transfer" && l.fromPlace !== null).map((l, i) => (
                <CircleMarker
                    key={i}
                    center={[l.fromPlace?.latitude, l.fromPlace?.longitude] as [number, number]}
                    radius={6}
                    pathOptions={{ color: "black", fillColor: "white", fillOpacity: 1 }}
                    pane="markerTopPane"
                />
            ))}
        </React.Fragment>
    );
}

export default ShowRoute;

/** End of file ShowRoute.tsx */
