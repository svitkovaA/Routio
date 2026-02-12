/**
 * @file MapInfoPopup.tsx
 * @brief Menu popup for assigning waypoints via map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import { Popup, useMapEvent } from "react-leaflet";
import { useState } from "react";
import { Waypoint } from "../../types/types";
import { useResult } from "../../ResultContext";

type MapInfoPopupProps = {
    waypoints: Waypoint[];                                                      // List of currently defined waypoints
    handleMapSelection: (lat: number, lon: number, index?: number) => boolean;  // Callback handling map based waypoint selection
}

function MapInfoPopup({
    waypoints,
    handleMapSelection
} : MapInfoPopupProps) {
    // Position state of the menu popup
    const [position, setPosition] = useState<[number, number] | null>(null);

    const { loading } = useResult();

    // Displays popup on right mouse click
    useMapEvent('contextmenu', (e) => {
        setPosition([e.latlng.lat, e.latlng.lng]);
    });

    /**
     * Assigns the selected map position to a waypoint
     * 
     * @param index Index of the waypoint to be updated
     * @param e Mouse click event
     */
    const handleSetWaypoint = (index: number, e: React.MouseEvent<HTMLButtonElement>) => {
        if (!position) {
            return;
        }
        e.stopPropagation();
        handleMapSelection(position[0], position[1], index);
        setPosition(null);
    };

    if (!position) {
        return null;
    }

    if (loading) {
        setPosition(null);
        return null;
    }

    return (
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
    );
}

export default MapInfoPopup;

/** End of file MapInfoPopup.tsx */
