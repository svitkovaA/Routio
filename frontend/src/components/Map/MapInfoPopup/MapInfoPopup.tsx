/**
 * @file MapInfoPopup.tsx
 * @brief Menu popup for assigning waypoints via map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef, useState } from "react";
import { Popup, useMapEvent } from "react-leaflet";
import { useResult } from "../../Contexts/ResultContext";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { useTranslation } from "react-i18next";
import { useInput } from "../../Contexts/InputContext";
import "./MapInfoPopup.css"

type MapInfoPopupProps = {
    handleMapSelection: (lat: number, lon: number, index?: number, target_waypoint_length?: number) => boolean;  // Callback handling map based waypoint selection
}

function MapInfoPopup({
    handleMapSelection
} : MapInfoPopupProps) {
    // Translation function
    const { t } = useTranslation();

    // Position state of the menu popup
    const [position, setPosition] = useState<[number, number] | null>(null);

    // Signalizes update needed
    const update = useRef<boolean>(null);

    // Waypoint length reference
    const length = useRef<number>(null);

    // Result context
    const { loading } = useResult();

    // Input context
    const { waypoints, addWaypoint } = useInput();

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

    /**
     * Adds waypoint handled by selection from context menu
     * 
     * @param e Mouse click event
     */
    const handleAddWaypoint = (e: React.MouseEvent<HTMLButtonElement>) => {
        if (!position) {
            return;
        }

        // Prevents popup close propagation
        e.stopPropagation();

        // Add waypoint to the second to last position
        addWaypoint(waypoints.length - 2);
        length.current = waypoints.length;
        update.current = true;
    };

    /**
     * Geocodes newly added waypoint
     */
    useEffect(() => {
        if (update.current && position && length.current !== null && length.current === waypoints.length - 1) {
            handleMapSelection(position[0], position[1], waypoints.length - 2, waypoints.length);
            setPosition(null);
        }
        
        update.current = null;
        length.current = null;
    }, [waypoints.length, handleMapSelection, position]);

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

                {/* Set as existing waypoint */}
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

                {/* Add new waypoint if maximum number is not already reached */}
                {waypoints.length < 10 &&
                    <button
                        className="popup-button context-menu"
                        onClick={(e) => handleAddWaypoint(e)}
                    >
                        {t("map.addWaypoint")}
                    </button>
                }
            </div>
        </Popup>
    );
}

export default MapInfoPopup;

/** End of file MapInfoPopup.tsx */
