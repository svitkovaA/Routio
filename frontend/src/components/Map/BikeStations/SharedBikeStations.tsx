/**
 * @file SharedBikeStations.tsx
 * @brief Displays shared bike stations on the map with clustering
 * @author Andrea Svitkova (xsvitka00)
 */

import { Marker, Popup, useMap } from "react-leaflet";
import type { MarkerCluster } from "leaflet.markercluster";
import { useInput } from "../../Contexts/InputContext";
import { createNextbikePin } from "../MapComponents";
import { memo, useEffect, useRef, useState } from "react";
import type { RefObject } from "react";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { Station } from "../../types/types";
import MarkerClusterGroup from "react-leaflet-cluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import { createClusterPin } from "../MapComponents";
import "./SharedBikeStations.css";

type StationPopupProps = {
    s: Station;                                     // Bike station data to be displayed in popup
    handleSetWaypoint: (
        station: Station,
        index: number,
        e: React.MouseEvent<HTMLButtonElement>
    ) => void;                                      // Function to assign station to an existing waypoint
    handleAddWaypoint: (station: Station, e: React.MouseEvent<HTMLButtonElement>) => void;  // Function to insert a new waypoint and assign station
    originRef: RefObject<"origin" | "destination">; // Reference storing whether station should be used as origin or destination
};

const StationPopup = memo(({
    s,
    handleSetWaypoint,
    handleAddWaypoint,
    originRef,
} : StationPopupProps) => {
    // Translation context
    const { t } = useTranslation();

    // User input context
    const { waypoints } = useInput();

    // Indicates whether station is considered as origin or destination
    const [selected, setSelected] = useState<"origin" | "destination">("origin");

    /**
     * Update originRef when mounted
     */
    useEffect(() => {
        originRef.current = selected;
    }, [originRef, selected]);

    return (
        <div className="shared-bike-popup-info">
            {/* Station basic information */}
            <div className="bicycle-name"><strong>{s.name}</strong></div>

            <div className="coordinates">
                Lat: {s.lat}<br/>
                Lon: {s.lon}
            </div>

            <div className="bicycle-section">
                <div className="bicycle-section-title">{t("map.station")}</div>
                <ToggleButtonGroup
                    className="bicycle-toggle-group"
                    value={selected}
                    exclusive
                    onChange={(_, val) => {
                        if (!val){
                            return;
                        }
                        originRef.current = val;
                        setSelected(val);
                    }}
                >
                    <ToggleButton
                        className="bicycle-toggle-button"
                        value="origin"
                        sx={{
                            "&.Mui-selected": {
                                backgroundColor: "var(--color-info)",
                                color: "white",
                            },

                            "&.Mui-selected:hover": {
                                backgroundColor: "var(--color-info)",
                                opacity: 0.9
                            }
                        }}
                    >
                        {t("map.pickUp")}
                    </ToggleButton>

                    <ToggleButton
                        className="bicycle-toggle-button"
                        value="destination"
                        sx={{
                            "&.Mui-selected": {
                                backgroundColor: "var(--color-info)",
                                color: "white",
                            },

                            "&.Mui-selected:hover": {
                                backgroundColor: "var(--color-info)",
                                opacity: 0.9
                            }
                        }}
                    >
                        {t("map.dropOff")}
                    </ToggleButton>
                </ToggleButtonGroup>
            </div>

            <div className="bicycle-section">
                <div className="bicycle-section-title">{t("map.routePosition")}</div>
                {/* Assign station to existing waypoint */}
                {waypoints.map((w, i) => (
                    <button
                        className="popup-button context-menu"
                        key={i}
                        onClick={(e) => handleSetWaypoint(s, i, e)}
                    >
                        {i === 0
                            ? t("map.setAsOrigin")
                            : i === waypoints.length - 1
                            ? t("map.setAsDestination")
                            : `${t("map.setAsWaypoint")} ${i}`}
                        {w.isActive && <LocationOnIcon sx={{ fontSize: 15 }} />}
                    </button>
                ))}

                {/* Add new waypoint if limit not reached */}
                {waypoints.length < 10 && (
                    <button 
                        className="popup-button context-menu"
                        onClick={(e) => handleAddWaypoint(s, e)}
                    >
                        {t("map.addWaypoint")}
                    </button>
                )}
            </div>
        </div>
    );
});

function SharedBikeStations() {
    // User input context
    const { 
        showBikeStations,
        bikeStations,
        waypoints,
        setWaypoints,
        clearWaypoint,
        addWaypoint
    } = useInput();

    //  Leaflet map instance
    const map = useMap();

    // Determines whether selected station will be origin or destination
    const originRef = useRef<"origin" | "destination">("origin");

    // Stores ids of stations already used as waypoints
    const [usedStationIds, setUsedStationIds] = useState<string[]>([]);

    /**
     * Update list of used station ids whenever waypoints change
     */
    useEffect(() => {
        setUsedStationIds(
            waypoints.filter(w => w.bikeStationId !== null).map(w => w.bikeStationId!)
        )
    }, [waypoints]);

    /**
     * Sets selected bike station as an existing waypoint
     * 
     * @param station Selected bike station
     * @param index Index of waypoint to update
     * @param e Mouse event
     */
    const handleSetWaypoint = (
        station: Station,
        index: number,
        e: React.MouseEvent<HTMLButtonElement>
    ) => {
        e.stopPropagation();

        // Ensure only one origin and destination station exists
        const sameIndex = waypoints.findIndex(w => w.origin === (originRef.current === "origin"));
        if (sameIndex >= 0) {
            clearWaypoint(sameIndex, true);
        }

        setWaypoints(prev => {
            if (index < 0 || index >= prev.length) {
                return prev;
            }

            // Update waypoints with station data
            const updated = [...prev];
            updated[index] = {
                ...updated[index],
                lat: station.lat,
                lon: station.lon,
                displayName: station.name,
                isActive: true,
                bikeStationId: station.id,
                origin: originRef.current === "origin"
            };

            return updated;
        });

        map.closePopup();
    };

    /**
     * Inserts a new waypoint and assigns it to the selected station
     * 
     * @param station Selected bike station
     * @param e Mouse event
     */
    const handleAddWaypoint = (station: Station, e: React.MouseEvent<HTMLButtonElement>) => {
        e.stopPropagation();

        // Ensure only one origin and destination station exists
        const sameIndex = waypoints.findIndex(w => w.origin === (originRef.current === "origin"));
        if (sameIndex >= 0) {
            clearWaypoint(sameIndex, true);
        }

        // Insert before destination
        const insertIndex = waypoints.length - 1;

        addWaypoint(waypoints.length - 2);

        setWaypoints(prev => {
            const index = insertIndex;

            if (index < 0 || index >= prev.length) {
                return prev;
            }

            // Update waypoints with station data
            const updated = [...prev];
            updated[index] = {
                ...updated[index],
                lat: station.lat,
                lon: station.lon,
                displayName: station.name,
                isActive: true,
                bikeStationId: station.id,
                origin: originRef.current === "origin"
            };

            return updated;
        });

        map.closePopup();
    };
    
    // Do not render component if bike stations are disabled
    if (!showBikeStations) {
        return null;
    }

    return (
        <MarkerClusterGroup
            chunkedLoading
            zoomToBoundsOnClick={false}
            showCoverageOnHover={false}

            // Custom cluster icon
            iconCreateFunction={(cluster: MarkerCluster) => {
                const count = cluster.getChildCount();

                // Cluster with one station
                if (count === 1) {
                    const marker = cluster.getAllChildMarkers()[0];
                    return marker.options.icon;
                }

                // Cluster with many stations
                return createClusterPin(count);
            }}

            // Custom cluster click behavior
            eventHandlers={{
                clusterclick: (e: { layer: MarkerCluster}) => {
                    const cluster = e.layer;
                    const count = cluster.getChildCount();

                    // When one station in cluster, open popup, zoom otherwise
                    if (count === 1) {
                        const marker = cluster.getAllChildMarkers()[0];
                        marker.openPopup();
                    }
                    else {
                        cluster.zoomToBounds();
                    }
                },
            }}
        >
            {bikeStations
                // Filter out already used stations
                .filter(s => !usedStationIds.includes(s.id))
                .map((s) => (
                    <Marker
                        key={s.id}
                        position={[s.lat, s.lon]}
                        icon={createNextbikePin()}
                    >
                        <Popup>
                            <StationPopup
                                s={s}
                                handleSetWaypoint={handleSetWaypoint}
                                handleAddWaypoint={handleAddWaypoint}
                                originRef={originRef}
                            />
                        </Popup>
                    </Marker>
                ))}
        </MarkerClusterGroup>
    );
}

export default SharedBikeStations;

/** End of file SharedBikeStations.tsx */
