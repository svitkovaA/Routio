/**
 * @file Map.tsx
 * @brief Main map component for displaying map, managing waypoints, layers, and route results
 * @author Andrea Svitkova (xsvitka00)
 */

import { MapContainer, TileLayer, ZoomControl, useMapEvent, Marker, Popup, ScaleControl } from 'react-leaflet'
import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { API_BASE_URL } from '../config/config';
import { useTranslation } from 'react-i18next';
import { InputText, ResultsType, RoutePreference, Waypoint } from '../types/types';
import { useLayers } from '../Controls/Layer/Layers';
import ShowRoute from './ShowRoute/ShowRoute';
import FitBound from './FitBound/FitBound';
import BikeStations from './BikeStations/BikeStations';
import 'leaflet/dist/leaflet.css';
import './Map.css';


L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

type mapProps = {
    sidebarOpen: boolean;
    openSidebar: () => void;
    waypoints: Waypoint[];
    setWaypoints: (value: Waypoint[]) => void;
    mapSelectionIndex: number;
    setMapSelectionIndex: (value: number) => void;
    results: ResultsType[];
    setResults: (value: ResultsType[] | ((prev: ResultsType[]) => ResultsType[])) => void;
    resultActiveIndex: number;
    showResults: boolean;
    selectedLayerIndex: number;
    selectedTripPatternIndex: number;
    handleMarkerRemove: (index: number) => void;
    arriveBy: boolean;
    useOwnBike: boolean;
    maxTransfers: number;
    selectedModes: string[];
    maxBikeDistance: number;
    bikeAverageSpeed: number;
    maxBikesharingDistance: number;
    bikesharingAverageSpeed: number;
    maxWalkDistance: number;
    walkAverageSpeed: number;
    bikesharingLockTime: number;
    bikeLockTime: number;
    preference: RoutePreference;
    setPreference: (value: RoutePreference) => void;
    closeResults: () => void;
};

function createPinIcon(label: string, translatedLabel?: string) {
    const startEndMarker = label === "START" || label === "END";
    const className = "marker " + (startEndMarker ? "start-end-marker" : "");
    let anchor: [number, number] = [14, 39];
    let popupAnchor: [number, number] = [0, -45];
    label = startEndMarker && translatedLabel ? translatedLabel : label
    if (startEndMarker) {
        anchor = [20,53];
        popupAnchor = [0, -55];
    }
    return L.divIcon({
        html: `
        <div class="${className}">
            <div class="marker-inner">${label}</div>
        </div>
        `,
        className: "",
        iconAnchor: anchor,
        popupAnchor: popupAnchor
    });
}

function SetViewOnClick({ onMapClick }: { onMapClick: (lat: number, lng: number) => boolean }) {
    const map = useMapEvent('click', (e) => {
        if (!onMapClick(e.latlng.lat, e.latlng.lng)) {
            map.setView(e.latlng, map.getZoom(), {
                animate: true,
                duration: 0.3
            });
        }
    });
    return null;
}

type MapInfoPopupProps = {
    waypoints: Waypoint[];
    handleMapSelection: (lat: number, lon: number, index?: number) => boolean;
}

function MapInfoPopup({
    waypoints,
    handleMapSelection
} : MapInfoPopupProps) {
    const [position, setPosition] = useState<[number, number] | null>(null);

    useMapEvent('contextmenu', (e) => {
        setPosition([e.latlng.lat, e.latlng.lng]);
    });

  const handleSetWaypoint = (index: number, e: React.MouseEvent<HTMLButtonElement>) => {
    if (!position) return;
    e.stopPropagation();
        handleMapSelection(position[0], position[1], index);
        setPosition(null);
  };

  return position ? (
    <Popup
      position={position}
      eventHandlers={{ remove: () => setPosition(null) }}
      closeButton={true}
    >
      <div className="map-popup">
        {waypoints.map((_, i) => (
          <button
            className="map-popup-button"
            key={i}
            onClick={(e) => handleSetWaypoint(i, e)}
          >
            {i === 0 ? "Set as origin" : i === waypoints.length - 1 ? "Set as destination" : `Set waypoint ${i}`}
          </button>
        ))}
      </div>
    </Popup>
  ) : null;
}

const center: L.LatLngTuple = [49.1951, 16.6068];
const defaultZoom = 13;

function Map({ 
    sidebarOpen,
    openSidebar, 
    waypoints, 
    setWaypoints, 
    mapSelectionIndex, 
    setMapSelectionIndex,
    results,
    setResults,
    resultActiveIndex,
    showResults,
    selectedLayerIndex,
    selectedTripPatternIndex,
    handleMarkerRemove,
    arriveBy,
    useOwnBike,
    maxTransfers,
    selectedModes,
    maxBikeDistance,
    bikeAverageSpeed,
    maxBikesharingDistance,
    bikesharingAverageSpeed,
    maxWalkDistance,
    walkAverageSpeed,
    bikesharingLockTime,
    bikeLockTime,
    preference,
    setPreference,
    closeResults
}: mapProps) {
    const { baseLayers, satelliteOverlay } = useLayers();
    const { t } = useTranslation();

    const startMarker = createPinIcon("START", t("map.markers.start") as string);
    const endMarker = createPinIcon("END", t("map.markers.end") as string);
    const popupRefs = useRef<(L.Popup | null)[]>([]);

    const handleMapSelection = (lat: number, lon: number, index?: number): boolean => {
        const targetIndex = index !== undefined ? index : mapSelectionIndex;
        if (targetIndex === -1) return false;
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

            if (window.innerWidth < 769) openSidebar();
            setMapSelectionIndex(-1);
        })
        .catch(console.error);
        closeResults();
    return true;
  };

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
            <MapInfoPopup 
                waypoints={waypoints}
                handleMapSelection={handleMapSelection}
            />
            <ZoomControl position="bottomright"/>
            <ScaleControl position="bottomleft" imperial={false} />

            <TileLayer 
                url={baseLayers[selectedLayerIndex].url}
                attribution={baseLayers[selectedLayerIndex].attribution}
            />

            {selectedLayerIndex === 2 && (
                <TileLayer 
                    url={satelliteOverlay.url}
                    attribution={satelliteOverlay.attribution}
                    opacity={0.6}
                />
            )}

            {showResults && waypoints.length > 1 && (
                <FitBound 
                    sidebarOpen={sidebarOpen}
                    results={results}
                    resultActiveIndex={resultActiveIndex}
                    selectedTripPatternIndex={selectedTripPatternIndex}
                />
            )}

            <SetViewOnClick 
                onMapClick={(lat: number, lon: number) => handleMapSelection(lat, lon)}
            />
            
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

            <ShowRoute 
                results={results}
                setResults={setResults}
                showResults={showResults}
                resultActiveIndex={resultActiveIndex}
                selectedTripPatternIndex={selectedTripPatternIndex}
            />
            <BikeStations 
                results={results}
                setResults={setResults}
                showResults={showResults}
                resultActiveIndex={resultActiveIndex}
                selectedTripPatternIndex={selectedTripPatternIndex}
                waypoints={waypoints}
                arriveBy={arriveBy}
                useOwnBike={useOwnBike}
                maxTransfers={maxTransfers}
                selectedModes={selectedModes}
                maxBikeDistance={maxBikeDistance}
                bikeAverageSpeed={bikeAverageSpeed}
                maxBikesharingDistance={maxBikesharingDistance}
                bikesharingAverageSpeed={bikesharingAverageSpeed}
                maxWalkDistance={maxWalkDistance}
                walkAverageSpeed={walkAverageSpeed}
                bikesharingLockTime={bikesharingLockTime}
                bikeLockTime={bikeLockTime}
                preference={preference}
                setPreference={setPreference}
            />
        </MapContainer>
    )
}

export default Map;

/** End of file Map.tsx */
