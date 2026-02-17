/**
 * @file BikeStations.tsx
 * @brief Displays bike stations on the map and allows changing origin and destination stations
 * @author Andrea Svitkova (xsvitka00)
 */

import { Fragment, useEffect, useState } from "react";
import { Marker, Popup, useMapEvent } from "react-leaflet";
import { useResult } from "../../ResultContext";
import { useChangeBikeStation } from "../../Routing/ChangeBikeStation";
import { createBikeStationPin, createSmallBikeStationPin } from "../MapComponents";
import "./BikeStations.css"

function BikeStations() {
    // Result context
    const {
        results,
        showResults,
        resultActiveIndex,
        selectedTripPatternIndex,
        pattern,
        loading
    } = useResult();

    // State handling map zoom level
    const [zoom, setZoom] = useState<number>(0);

    // State handling visibility flags for alternative bike stations
    const [showBikeStations, setShowBikeStations] = useState<boolean[]>([]);

    // Handler for changing selected bike station
    const changeBikeStation = useChangeBikeStation();

    // Updates zoom state when map zoom level changes
    useMapEvent("zoomend", (e) => {
        setZoom(e.target.getZoom());
    });
    
    /**
     * Initializes bike station visibility flags when route changes
     */
    useEffect(() => {
        const currentLegs = pattern?.legs ?? [];
        if (currentLegs.length > 0) {
            setShowBikeStations(currentLegs.map(() => false));
        }
    }, [results, resultActiveIndex, selectedTripPatternIndex, pattern?.legs]);

    // Do not render if no routing results are displayed
    if (!showResults) {
        return null;
    }

    /**
     * Toggles visibility of alternative bike stations for a given leg
     *
     * @param index Index of the route leg
     */
    const invertBikeStationAtIndex = (index: number) => {
        setShowBikeStations(prev => prev.map((v, i) => (i === index ? !v : v)));
    };

    return (
        <>
            {pattern?.legs.map((leg, index) => {
                if (!leg || leg.mode !== "wait" || !leg?.bikeStationInfo) {
                    return null;
                }

                const origin = leg.bikeStationInfo.origin
                const selectedIndex = leg.bikeStationInfo.selectedBikeStationIndex;
                const rack = leg.bikeStationInfo.rack;

                return (
                    <Fragment key={`${index}`}>
                        {/* Currently selected bike station */}
                        <Marker
                            position={[leg.bikeStationInfo.latitude, leg.bikeStationInfo.longitude]}
                            icon={createBikeStationPin(origin)}
                        >
                            <Popup autoPan={false}>
                                <button
                                    onClick={() => invertBikeStationAtIndex(index)}
                                    disabled={loading}
                                >
                                    {showBikeStations[index] ? "Hide bike stations" : "Show bike stations"}
                                </button>
                            </Popup>
                        </Marker>

                        {/* Alternative bike stations */}
                        {showBikeStations[index] && leg?.bikeStationInfo.bikeStations.map((station, bikeStationIndex) => 
                            bikeStationIndex !== selectedIndex && zoom > 12 &&(
                                <Marker
                                    key={`${bikeStationIndex}`}
                                    position={[station.place.latitude, station.place.longitude]}
                                    icon={createSmallBikeStationPin(origin)}  
                                >
                                    {/* Popup information */}
                                    <Popup autoPan={false}>
                                        Index: {bikeStationIndex} <br/>
                                        Score: {station.score} <br/>
                                        Distance: {station.distance} <br/>
                                        {rack ? (
                                            <>Capacity:  {station.place?.capacity} <br/> </>
                                        ) : (
                                            <>BikesAvailable: {station.place.bikesAvailable} <br/> </>
                                        )}
                                        <button 
                                            className="popup-button"
                                            onClick={() => changeBikeStation(origin, bikeStationIndex, leg.bikeStationInfo?.bikeStations as any, index)}
                                        >
                                            Set as {origin ? "origin" : "destination"} bike station
                                        </button>
                                    </Popup>
                                </Marker>
                            )
                        )}
                    </Fragment>
                )
            })}
        </>
    );
}

export default BikeStations;

/** End of file BikeStations.tsx */
