/**
 * @file Map.tsx
 * @brief Main map component for map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import { MapContainer, TileLayer, ZoomControl, Marker, Popup, ScaleControl } from 'react-leaflet'
import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL } from '../config/config';
import { InputText } from '../types/types';
import { useLayers } from '../Controls/Layer/Layers';
import ShowRoute from './ShowRoute/ShowRoute';
import FitBound from './FitBound/FitBound';
import BikeStations from './BikeStations/BikeStations';
import { useInput } from '../InputContext';
import { useSettings } from '../SettingsContext';
import { useResult } from '../ResultContext';
import MapInfoPopup from './MapInfoPopup/MapInfoPopup';
import { createPinIcon, SetViewOnClick } from './MapComponents';
import 'leaflet/dist/leaflet.css';
import './Map.css';

L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

type MapProps = {
    sidebarOpen: boolean;                           // State whether the sidebar is currently opened
    openSidebar: () => void;                        // Callback used to open the sidebar
    handleMarkerRemove: (index: number) => void;    // Removes or clears a waypoint marker
    closeResults: () => void;                       // Clear trip results
};

function Map({ 
    sidebarOpen,
    openSidebar,
    handleMarkerRemove,
    closeResults 
}: MapProps) {
    const { t } = useTranslation();

    // Contexts
    const { showResults } = useResult();
    const { selectedLayerIndex } = useSettings();
    const { baseLayers, satelliteOverlay } = useLayers();
    const {
        waypoints, 
        setWaypoints, 
        mapSelectionIndex, 
        setMapSelectionIndex,
    } = useInput();

    const center: L.LatLngTuple = [49.1951, 16.6068];
    const defaultZoom = 13;

    // Custom marker icons
    const startMarker = createPinIcon("START", t("map.markers.start") as string);
    const endMarker = createPinIcon("END", t("map.markers.end") as string);

    // Reference to popup instance 
    const popupRefs = useRef<(L.Popup | null)[]>([]);

    /**
     * Handles selection of the location on the map
     * 
     * @param lat Latitude of the selected location
     * @param lon Longitude of the selected location
     * @param index Waypoint index
     * @returns True if the click was handled false otherwise
     */
    const handleMapSelection = (lat: number, lon: number, index?: number): boolean => {
        const targetIndex = index !== undefined ? index : mapSelectionIndex;
        if (targetIndex === -1) 
            return false;
        fetch(`${API_BASE_URL}/geocode/latLon?lat=${lat}&lon=${lon}`)
            .then((res) => {
                if (!res.ok) throw new Error("Network response was not ok");
                return res.json();
            })
            .then((data: InputText) => {
                const displayName = [data.street, data.city].filter(Boolean).join(", ");

                const newWaypoints = [...waypoints];
                newWaypoints[targetIndex] = {
                ...newWaypoints[targetIndex], lat, lon, displayName, isActive: true
                };
                setWaypoints(newWaypoints);

                // Automatically open sidebar on small screens
                if (window.innerWidth < 769) 
                    openSidebar();
                setMapSelectionIndex(-1);
            })
            .catch(console.error);
        closeResults();
        return true;
    };

    /**
     * Updates cursor style while map selection mode is active
     */
    useEffect(() => {
        let cursor = "";
        if (mapSelectionIndex !== -1) {
            cursor="crosshair";
        }
        const elements = document.getElementsByClassName("leaflet-grab");
        for (let i = 0; i < elements.length; i++) {
            (elements[i] as HTMLElement).style.cursor = cursor;
        }
    }, [mapSelectionIndex])

    return (
        <MapContainer center={center} zoom={defaultZoom} zoomControl={false} id="map" className={mapSelectionIndex !== -1 ? "selected" : ""}>
            {/* Popup information during waypoint selection */}
            <MapInfoPopup 
                waypoints={waypoints}
                handleMapSelection={handleMapSelection}
            />
            <ZoomControl position="bottomright"/>
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
            
            {/* Render waypoint markers */}
            {waypoints.map((w, i) =>
                w.isActive && (
                    <Marker
                        key={i}
                        position={[w.lat, w.lon]}
                        icon={i === 0 ? startMarker : i !== waypoints.length - 1 ? createPinIcon(i.toString()) : endMarker}
                    >
                        <Popup
                            ref={el => {
                                popupRefs.current[i] = el 
                            }}
                        >
                            {w.displayName} <br/>
                            Lat: {w.lat.toFixed(5)} <br/>
                            Lon: {w.lon.toFixed(5)} <br/>
                            <button 
                                className="popup-button"
                                onClick={() => {
                                    handleMarkerRemove(i);
                                    popupRefs.current[i]?.remove();
                                }}                          
                            >
                                {waypoints.length === 2 ? "Clear waypoint" : "Remove waypoint"}
                            </button>
                        </Popup>
                    </Marker>
                )
            )}

            {/* Route visualisation */}
            <ShowRoute />

            {/* Bicycle stations visualisation */}
            <BikeStations />
        </MapContainer>
    )
}

export default Map;

/** End of file Map.tsx */
