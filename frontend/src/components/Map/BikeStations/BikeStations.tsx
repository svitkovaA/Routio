/**
 * @file BikeStations.tsx
 * @brief Displays bike stations on the map and allows changing origin and destination stations
 * @author Andrea Svitkova (xsvitka00)
 */

import L from "leaflet";
import { Fragment, useEffect, useState } from "react";
import { Marker, Popup, useMapEvent } from "react-leaflet";
import { useTranslation } from "react-i18next";
import { useResult } from "../../Contexts/ResultContext";
import { useChangeBikeStation } from "../../Routing/ChangeBikeStation";
import { createBikeStationPin, createSmallBikeStationPin } from "../MapComponents";
import CustomLeafletTooltip from "../../CustomTooltip/CustomLeafletTooltip";
import CustomTooltip from "../../CustomTooltip/CustomTooltip";
import "./BikeStations.css";

type BikeStationsProps = {
    tooltipHandler: (id: string) => L.LeafletEventHandlerFnMap;
};

function BikeStations({
    tooltipHandler
} : BikeStationsProps) {
    //Translation function
    const { t } = useTranslation();

    // Result context
    const {
        showResults,
        pattern,
        loading,
        showBikeStations,
        setShowBikeStations
    } = useResult();

    // State handling map zoom level
    const [zoom, setZoom] = useState<number>(0);

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
        const currentLegs = pattern?.originalLegs ?? [];
        if (currentLegs.length > 0) {
            setShowBikeStations(currentLegs.map(() => false));
        }
    }, [pattern?.originalLegs, setShowBikeStations]);

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
            {pattern?.originalLegs.map((leg, index) => {
                if (!leg || leg.mode !== "wait" || !leg?.bikeStationInfo) {
                    return null;
                }

                const origin = leg.bikeStationInfo.origin
                const selectedIndex = leg.bikeStationInfo.selectedBikeStationIndex;
                const rack = leg.bikeStationInfo.rack;
                const selectedStation = leg.bikeStationInfo.bikeStations[selectedIndex];
                const capacity = selectedStation.place.capacity;

                return (
                    <Fragment key={`${index}`}>
                        {/* Currently selected bike station */}
                        <Marker
                            position={[leg.bikeStationInfo.latitude, leg.bikeStationInfo.longitude]}
                            icon={createBikeStationPin(origin)}
                            eventHandlers={tooltipHandler(`bike-main-${index}`)}
                        >
                            <CustomLeafletTooltip>
                                {origin ? t("tooltips.map.originBikeStation") : t("tooltips.map.destinationBikeStation")}
                            </CustomLeafletTooltip>

                            <Popup>
                                <strong>{selectedStation.place.name}</strong> <br/>
                                <div className="bike-stations-popup-info">
                                    <div className="bike-stations-coords">
                                        <div>{t("map.lat")}: {leg.bikeStationInfo?.latitude.toFixed(5)}</div>
                                        <div>{t("map.lon")}: {leg.bikeStationInfo?.longitude.toFixed(5)}</div>
                                    </div>
                                    {leg.bikeStationInfo.origin ? (
                                        <>
                                            <div className="bike-stations-bike-count">
                                                <div className="count-header">{t("map.now")}</div>
                                                <div className="count">
                                                    {selectedStation.place.bikesAvailable !== undefined && selectedStation.place.bikesAvailable < 10 ? selectedStation.place.bikesAvailable : "10+"}
                                                </div>
                                            </div>
                                            <div className="bike-stations-bike-count">
                                                <div className="count-header">{t("map.predicted")}</div>
                                                <div className="count">
                                                    {selectedStation.place.predictedBikes !== null ? (
                                                        <>
                                                        {selectedStation.place.predictedBikes !== undefined && selectedStation.place.predictedBikes < 10 ? selectedStation.place.predictedBikes : "10+"}
                                                        </>
                                                    ) : (
                                                        <CustomTooltip title={t("tooltips.map.noPrediction")}>
                                                            <span>--</span>
                                                        </CustomTooltip>
                                                    )}
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="bike-stations-bike-count">
                                            <div className="count-header">{t("map.capacity")}</div>
                                            <div className="count">
                                            {capacity !== undefined && capacity < 10 ? capacity : "10+"}
                                            </div>
                                        </div>
                                    )}
                                </div>
                                {!loading && leg?.bikeStationInfo.bikeStations.length > 1 && (
                                    <button
                                        className="popup-button"
                                        onClick={() => invertBikeStationAtIndex(index)}
                                    >
                                        {rack
                                            ? (showBikeStations[index] ? t("map.hideBikeRacks") : t("map.showBikeRacks"))
                                            : (showBikeStations[index] ? t("map.hideBikeStations") : t("map.showBikeStations"))
                                        }
                                    </button>
                                )}
                            </Popup>
                        </Marker>

                        {/* Alternative bike stations */}
                        {showBikeStations[index] && leg?.bikeStationInfo.bikeStations.map((station, bikeStationIndex) => 
                            bikeStationIndex !== selectedIndex && zoom > 12 &&(
                                <Marker
                                    key={`${bikeStationIndex}`}
                                    position={[station.place.latitude, station.place.longitude]}
                                    icon={createSmallBikeStationPin(origin)}
                                    eventHandlers={tooltipHandler(`bike-alternatives-${index}-${bikeStationIndex}`)}
                                >
                                    <CustomLeafletTooltip>
                                        {origin ? t("tooltips.map.alternativeOriginBikeStation") : t("tooltips.map.alternativeDestinationBikeStation")}
                                    </CustomLeafletTooltip>

                                    {/* Popup information */}
                                    <Popup>
                                        <strong>{station.place.name}</strong> <br/>
                                        <div className="bike-stations-popup-info">
                                            <div className="bike-stations-coords">
                                                <div>{t("map.lat")}: {station.place.latitude.toFixed(5)}</div>
                                                <div>{t("map.lon")}: {station.place.longitude.toFixed(5)}</div>
                                            </div>
                                            {leg.bikeStationInfo?.origin ? (
                                                <>
                                                    <div className="bike-stations-bike-count">
                                                        <div className="count-header">{t("map.now")}</div>
                                                        <div className="count">
                                                            {station.place.bikesAvailable !== undefined && station.place.bikesAvailable < 10 ? station.place.bikesAvailable : "10+"}
                                                        </div>
                                                    </div>
                                                    <div className="bike-stations-bike-count">
                                                        <div className="count-header">{t("map.predicted")}</div>
                                                        <div className="count">
                                                            {station.place.predictedBikes !== null ? (
                                                                <>
                                                                    {station.place.predictedBikes !== undefined && station.place.predictedBikes < 10 ? station.place.predictedBikes : "10+"}
                                                                </>
                                                            ) : (
                                                                <CustomTooltip title={t("tooltips.map.noPrediction")}>
                                                                    <span>--</span>
                                                                </CustomTooltip>
                                                            )}
                                                        </div>
                                                    </div>
                                                </>
                                            ) : (
                                                <div className="bike-stations-bike-count">
                                                    <div className="count-header">{t("map.capacity")}</div>
                                                    <div className="count">
                                                    {station.place.capacity !== undefined && station.place.capacity < 10 ? station.place.capacity : "10+"}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <button 
                                            className="popup-button"
                                            onClick={() => {
                                                if (!leg.bikeStationInfo?.bikeStations) {
                                                    return;
                                                }
                                                changeBikeStation(origin, bikeStationIndex, leg.bikeStationInfo.bikeStations, index)
                                            }}
                                        >
                                            {leg.bikeStationInfo?.origin ? t("map.setAsOriginStation")
                                            : rack && !leg.bikeStationInfo?.origin ? t("map.setAsDestinationRack")
                                            : t("map.setAsDestinationStation")}
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
