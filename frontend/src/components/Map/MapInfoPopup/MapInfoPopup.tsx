import { useState } from "react";
import { Waypoint } from "../../types/types";
import { Popup, useMapEvent } from "react-leaflet";

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
        if (!position) {
            return;
        }
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

export default MapInfoPopup;