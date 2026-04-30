/**
 * @file Map.tsx
 * @brief Main map component for map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ScaleControl, Polyline, useMapEvent } from 'react-leaflet'
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import { useMediaQuery } from '@mui/material';
import { API_BASE_URL, PUBLIC_URL } from '../config/config';
import type { Suggestion } from '../types/types';
import { useLayers } from '../Controls/Layer/Layers';
import ShowRoute from './ShowRoute/ShowRoute';
import FitBound from './FitBound/FitBound';
import BikeStations from './BikeStations/BikeStations';
import MapInfoPopup from './MapInfoPopup/MapInfoPopup';
import CustomLeafletTooltip from '../CustomTooltip/CustomLeafletTooltip';
import { createPinIcon, createVehiclePositionIcon } from './MapComponents';
import { timelineIcons } from '../Sidebar/Planning/Icons/IconMappings';
import CustomZoomControl from './CustomZoomControl/CustomZoomControl';
import { useInput } from '../Contexts/InputContext';
import { useSettings } from '../Contexts/SettingsContext';
import { useResult } from '../Contexts/ResultContext';
import { useNotification } from "../Contexts/NotificationContext";
import { NW_LAT, NW_LON, SE_LAT, SE_LON } from "../config/config";
import SharedBikeStations from './BikeStations/SharedBikeStations';
import { Polygon } from "react-leaflet";
import 'leaflet/dist/leaflet.css';
import './Map.css';
import { JMKBounds } from './JMKBounds';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
    iconRetinaUrl: markerIcon2x,
    iconUrl: markerIcon,
    shadowUrl: markerShadow,
});

/**
 * Handles map click interaction
 * If the callback returns false the map is moved animated to the clicked position
 * 
 * @param onMapClick Callback handling map click event
 */
function SetViewOnClick({ onMapClick }: { onMapClick: (lat: number, lng: number) => boolean }) {
    useMapEvent('click', (e) => {
        const map = e.target;
        // Move map to the position
        if (!onMapClick(e.latlng.lat, e.latlng.lng)) {
            map.setView(e.latlng, map.getZoom(), {
                animate: true,
                duration: 0.3
            });
        }
    });
    return null;
}

type MapProps = {
    sidebarOpen: boolean;                           // Indicates whether the sidebar is currently open
    openSidebar: () => void;                        // Callback used to open the sidebar
    handleMarkerRemove: (index: number) => void;    // Removes or clears a waypoint marker
};

function Map({ 
    sidebarOpen,
    openSidebar,
    handleMarkerRemove,
}: MapProps) {
    // Translation function
    const { t } = useTranslation();

    // Whole world bounds
    const worldBounds: [number, number][] = [
        [-90, -180],
        [-90, 180],
        [90, 180],
        [90, -180],
    ];

    // Contexts
    const {
        showResults,
        vehicleRealtimeData,
        closeResults,
        loading 
    } = useResult();

    const { selectedLayerIndex } = useSettings();

    const { 
        baseLayers,
        satelliteOverlay
    } = useLayers();

    const {
        waypoints, 
        setWaypoints, 
        mapSelectionIndex, 
        setMapSelectionIndex,
        setFieldErrors
    } = useInput();

    const { showNotification } = useNotification();

    // Default map center
    const defaultCenter: L.LatLngTuple = [49.1951, 16.6068];

    // Default map zoom
    const defaultZoom = 13;

    // Custom marker icons
    const startMarker = createPinIcon("START", waypoints[0].isPreview, t("map.markers.start") as string);
    const endMarker = createPinIcon("END", waypoints[waypoints.length - 1].isPreview, t("map.markers.end") as string);

    // Reference to popup instance 
    const popupRefs = useRef<(L.Popup | null)[]>([]);

    // Reference used to store tooltip opening timer
    const tooltipTimers = useRef<Record<string, NodeJS.Timeout | null>>({});
    const currentlyOpenTooltip = useRef<L.Marker | null>(null);

    const isDesktop = useMediaQuery("(min-width:768px)");

    const tooltipHandler = (id: string): L.LeafletEventHandlerFnMap => ({
        // Triggered when popup is open
        popupopen: (e) => {
            e.target._popupOpen = true;
            e.target.getTooltip()?.setOpacity(0);
        },

        // Triggered when popup is closed
        popupclose: (e) => {
            e.target._popupOpen = false;
        },

        // Triggered when mouse enters marker area
        mouseover: (e) => {
            if (e.target._popupOpen) {
                return;
            }

            // Starts delayed tooltip opening
            tooltipTimers.current[id] = setTimeout(() => {
                if (!e.target._popupOpen) {

                    // Ensures only one tooltip at the time
                    if (currentlyOpenTooltip.current && currentlyOpenTooltip.current !== e.target) {
                        currentlyOpenTooltip.current.getTooltip()?.setOpacity(0);
                        currentlyOpenTooltip.current.closeTooltip();
                    }

                    // Show and open tooltip
                    e.target.getTooltip()?.setOpacity(1);
                    e.target.openTooltip();

                    currentlyOpenTooltip.current = e.target;
                }
            }, 800);
        },

        // Triggered when mouse leaves marker area
        mouseout: (e) => {
            const timer = tooltipTimers.current[id];

            // Cancel pending tooltip delay
            if (timer) {
                clearTimeout(timer);
                tooltipTimers.current[id] = null;
            }

            // Hide and close tooltip
            e.target.getTooltip()?.setOpacity(0);
            e.target.closeTooltip();

            if (currentlyOpenTooltip.current === e.target) {
                currentlyOpenTooltip.current = null;
            }
        }
    });

    /**
     * Handles location selection on the map
     * 
     * @param lat Latitude of the selected location
     * @param lon Longitude of the selected location
     * @param index Waypoint index
     * @param target_waypoint_length Target length
     * @returns True if the selection was handled, false otherwise
     */
    const handleMapSelection = (lat: number, lon: number, index?: number, target_waypoint_length?: number): boolean => {
        // Resolve target waypoint index
        const targetIndex = index !== undefined ? index : mapSelectionIndex;

        // No active click, ignore selection
        if (targetIndex === -1) {
            return false;
        }

        // Apply bounding box for selection
        if (lon < NW_LON || lon > SE_LON || lat < SE_LAT || lat > NW_LAT) {
            showNotification(t("warnings.bbox"), "warning");
            // Cancel map selection mode
            setMapSelectionIndex(-1);
            return true;
        }
        
        /**
         * Updates the selected waypoint with resolved display name
         * 
         * @param displayName Address resolved from reverse geocoding
         */
        const updateWaypoints = (displayName: string, initial: boolean = false) => {
            // Update waypoint state
            setWaypoints(prev => {
                if (targetIndex < 0 || targetIndex >= prev.length || !prev[targetIndex] || (target_waypoint_length !== undefined && target_waypoint_length !== prev.length)) {
                    return prev;
                }

                const updated = [...prev];
                updated[targetIndex] = {
                    ...updated[targetIndex],
                    lat,
                    lon,
                    displayName,
                    isActive: true,
                    bikeStationId: null,
                    origin: null
                };

                return updated;
            });
            if (initial) {
                // Automatically open sidebar on mobile devices
                if (window.innerWidth < 768) {
                    openSidebar();
                }

                // Cancel map selection mode
                setMapSelectionIndex(-1);
            }
        };

        updateWaypoints(t("map.geocode"), true);

        // Reverse geocoding request to backend API
        fetch(`${API_BASE_URL}/geocode/latLon?lat=${lat}&lon=${lon}`)
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Network response was not ok");
                }
                return res.json();
            })
            .then((data: Suggestion) => {
                // Build display name from street and city information
                let displayName = data.name;
                // Prevent empty fields
                if (displayName.length === 0) {
                    displayName = `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
                    showNotification(t("warnings.nominatim"), "warning");
                }
                updateWaypoints(displayName);
            })
            .catch(() => {
                // Fallback to use coordinates if reverse geocoding fails
                showNotification(t("warnings.nominatim"), "warning");
                const displayName = `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
                updateWaypoints(displayName);
            });

        // Clear validation error for the target field
        setFieldErrors(prev => prev.filter((p) => p !== targetIndex));

        // Close route results after selecting new location
        closeResults();

        return true;
    };

    /**
     * Updates cursor style while map selection mode is active
     */
    useEffect(() => {
        // Determine cursor style based on selection state
        const cursor = mapSelectionIndex !== -1 ? `url(${PUBLIC_URL}img/marker.svg) 20 35, auto` : "";

        // Overwrite cursor style
        const elements = document.querySelectorAll(".leaflet-grab, .map-overlay");
        for (let i = 0; i < elements.length; i++) {
            (elements[i] as HTMLElement).style.cursor = cursor;
        }
    }, [mapSelectionIndex]);

    return (
        <MapContainer
            center={defaultCenter}
            zoom={defaultZoom}
            zoomControl={false}
            minZoom={5}
            maxBounds={[
                [-90, -180],  // South west coordinate
                [90, 180]     // North east coordinate
            ]}
            maxBoundsViscosity={0.5}
            className={"map" + (mapSelectionIndex !== -1 ? "selected" : "")}
        >
            {/* Popup information during waypoint selection */}
            <MapInfoPopup
                handleMapSelection={handleMapSelection}
            />
            
            {/* Zoom handler */}
            {isDesktop && (
                <CustomZoomControl />
            )}

            {/* Scale indicator */}
            <ScaleControl position="bottomleft" imperial={false} />

            {/* Base map layer */}
            <TileLayer
                url={baseLayers[selectedLayerIndex].url}
                attribution={baseLayers[selectedLayerIndex].attribution}
            />

            {/* Optional satellite overlay */}
            {selectedLayerIndex === 2 && (
                <TileLayer
                    url={satelliteOverlay.url}
                    attribution={satelliteOverlay.attribution}
                    opacity={0.6}
                />
            )}

            {/* Automatically fit map bounds to route */}
            {showResults && waypoints.length > 1 && (
                <FitBound 
                    sidebarOpen={sidebarOpen}
                />
            )}

            {/* Handle map click events */}
            <SetViewOnClick 
                onMapClick={(lat: number, lon: number) => handleMapSelection(lat, lon)}
            />

            {/* Shared bicycle stations in input form */}
            <SharedBikeStations />
            
            {/* Render waypoint markers */}
            {waypoints.map((w, i) =>
                (w.isActive || w.isPreview) && (
                    <Marker
                        key={`${i}-${w.lat}-${w.lon}`}
                        position={[w.lat, w.lon]}
                        icon={i === 0 ? startMarker : i !== waypoints.length - 1 ? createPinIcon(i.toString(), w.isPreview) : endMarker}
                        eventHandlers={tooltipHandler(`waypoint-${i}`)}
                    >
                        <CustomLeafletTooltip>
                            {t("tooltips.map.marker")}
                        </CustomLeafletTooltip>

                        {/* Popup for waypoint marker */}
                        <Popup
                            ref={el => {
                                popupRefs.current[i] = el 
                            }}
                        >
                            <strong>{w.displayName}</strong> <br/>
                            <div className="map-lat-lon">
                                Lat: {w.lat.toFixed(5)} <br/>
                                Lon: {w.lon.toFixed(5)} <br/>
                            </div>
                            <button 
                                className="popup-button"
                                onClick={() => {
                                    handleMarkerRemove(i);
                                    popupRefs.current[i]?.remove();
                                }}
                                disabled={loading}
                            >
                                {waypoints.length === 2 ? t("map.clearWaypoint") : t("map.removeWaypoint")}
                            </button>
                        </Popup>
                    </Marker>
                )
            )}

            {/* Route visualisation */}
            <ShowRoute />

            {/* Bicycle stations visualisation */}
            <BikeStations
                tooltipHandler={tooltipHandler}
            />

            {/* Border around JMK region */}
            <Polyline
                className="map-overlay"
                key="JMKBounds"
                positions={JMKBounds}
                color="var(--color-info)"
                pathOptions={{ weight: 2 }}
            />

            {/* Grey overlay outside JMK */}
            <Polygon
                className="map-overlay"
                positions={[worldBounds, JMKBounds]}
                pathOptions={{
                    color: "none",
                    fillColor: "grey",
                    fillOpacity: 0.3,
                }}
            />

            {/* Actual vehicle position visualisation */}
            {vehicleRealtimeData.filter(p => p.lat > 0 && p.lon > 0).map((p) => (
                <Marker
                    key={`${p.tripId}`}
                    position={[p.lat, p.lon]}
                    icon={createVehiclePositionIcon(p.publicCode, p.color)}
                    eventHandlers={tooltipHandler(`vehicle-${p.tripId}`)}
                >
                    <CustomLeafletTooltip>
                        {t("tooltips.map.vehiclePosition")}
                    </CustomLeafletTooltip>

                    {/* Popup for vehicle position */}
                    <Popup>
                        <div className="vehicle-position-popup">
                            <div className="vehicle-position-popup-left">
                                <div
                                    className="vehicle-position-popup-public-code"
                                    style={{ backgroundColor: p.color }}
                                >
                                    {p.publicCode}
                                </div>
                                <div className="vehicle-position-popup-icon">
                                    {timelineIcons[p.mode]}
                                </div>
                            </div>
                            <div className="vehicle-position-popup-right">
                                <div>
                                    <strong>{p.direction}</strong>
                                </div>
                                <div>
                                    {p.delay && p.delay > 0 ? `${t("map.ptCurrentDelay")}: ${p.delay} min` : t("map.ptWithoutDelay")}
                                </div>
                            </div>
                        </div>
                    </Popup>
                </Marker>
            ))}
        </MapContainer>
    )
}

export default Map;

/** End of file Map.tsx */
