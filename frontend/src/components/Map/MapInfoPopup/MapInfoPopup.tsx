/**
 * @file MapInfoPopup.tsx
 * @brief Menu popup for assigning waypoints via map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { Popup, useMapEvent } from "react-leaflet";
import { Waypoint } from "../../types/types";
import { useResult } from "../../Contexts/ResultContext";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { useTranslation } from "react-i18next";
import "./MapInfoPopup.css"

type MapInfoPopupProps = {
    waypoints: Waypoint[];                                                      // List of currently defined waypoints
    handleMapSelection: (lat: number, lon: number, index?: number) => boolean;  // Callback handling map based waypoint selection
}

function MapInfoPopup({
    waypoints,
    handleMapSelection
} : MapInfoPopupProps) {
    // Translation function
    const { t } = useTranslation();

    // Position state of the menu popup
    const [position, setPosition] = useState<[number, number] | null>(null);

    // Result context
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
        // Prevents popup close propagation
        e.stopPropagation();
        
        handleMapSelection(position[0], position[1], index);
        setPosition(null);
    };

    // Do not render popup if no position is selected
    if (!position) {
        return null;
    }

    // Automatically close popup during loading state
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
            <div className="map-popup selection">
                <strong>{t("map.selectPosition")}</strong>
                {waypoints.map((w, i) => (
                    <button
                        className="popup-button context-menu"
                        key={i}
                        onClick={(e) => handleSetWaypoint(i, e)}
                    >
                        {i === 0 ? t("map.setAsOrigin") : i === waypoints.length - 1 ? t("map.setAsDestination") : `${t("map.setAsWaypoint")} ${i}`}
                        {w.isActive && <LocationOnIcon sx={{ fontSize: 15 }} />}
                    </button>
                ))}
            </div>
        </Popup>
    );
}

export default MapInfoPopup;

/** End of file MapInfoPopup.tsx */
