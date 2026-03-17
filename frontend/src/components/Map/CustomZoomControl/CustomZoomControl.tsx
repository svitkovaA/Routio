/**
 * @file CustomZoomControl.tsx
 * @brief Custom zoom control component
 * @author Andrea Svitkova (xsvitka00)
 */

import { useCallback, useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import { useTranslation } from "react-i18next";
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import CustomTooltip from "../../CustomTooltip/CustomTooltip";
import "./CustomZoomControl.css";

function CustomZoomControl() {
    // Function translation
    const { t } = useTranslation();

    // Leaflet map instance
    const map = useMap();

    // References for elements and interval
    const containerRef = useRef<HTMLDivElement>(null);
    const zoomInButtonRef = useRef<HTMLButtonElement>(null);
    const zoomOutButtonRef = useRef<HTMLButtonElement>(null);
    const zoomInterval = useRef<ReturnType<typeof setInterval> | null>(null);

    /**
     * Start continuous zooming in or out
     * 
     * @param type Zoom action
     */
    const startZoom = useCallback((type: "in" | "out") => {
        // Prevent multiple intervals running simultaneously
        if (zoomInterval.current) {
            return;
        }

        // Perform initial zoom step
        if (type === "in") {
            map.zoomIn();
        }
        else {
            map.zoomOut();
        }

        // Start continuous zooming
        zoomInterval.current = setInterval(() => {
            if (type === "in") {
                map.zoomIn();
            }
            else {
                map.zoomOut();
            }
        }, 50);
    }, [map]);

    /**
     * Stop continuous zooming
     */
    const stopZoom = useCallback(() => {
        if (zoomInterval.current) {
            clearInterval(zoomInterval.current);
            zoomInterval.current = null;
        }
    }, []);

    /**
     * Disable map interactions on controls
     */
    useEffect(() => {
        if (!containerRef.current) {
            return;
        }

        L.DomEvent.disableClickPropagation(containerRef.current);
        L.DomEvent.disableScrollPropagation(containerRef.current);
    }, []);

    /**
     * Attach mouse events to buttons
     */
    useEffect(() => {
        const zoomInButton = zoomInButtonRef.current;
        const zoomOutButton = zoomOutButtonRef.current;

        if (!zoomInButton || !zoomOutButton) {
            return;
        }

        // Handle press on zoom in
        const handleZoomInMouseDown = (e: MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            startZoom("in");
        };

        // Handle press on zoom out
        const handleZoomOutMouseDown = (e: MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            startZoom("out");
        };

        // Stop zooming when mouse is released anywhere
        const handleMouseUp = () => {
            stopZoom();
        };

        // Register listeners
        zoomInButton.addEventListener("mousedown", handleZoomInMouseDown);
        zoomOutButton.addEventListener("mousedown", handleZoomOutMouseDown);
        window.addEventListener("mouseup", handleMouseUp);

        // Cleanup listeners on unmount
        return () => {
            zoomInButton.removeEventListener("mousedown", handleZoomInMouseDown);
            zoomOutButton.removeEventListener("mousedown", handleZoomOutMouseDown);
            window.removeEventListener("mouseup", handleMouseUp);
        };
    }, [map, startZoom, stopZoom]);

    return (
        <div ref={containerRef} className="custom-zoom-control">
            <CustomTooltip title={t("tooltips.controls.map.zoomIn")} placement="left">
                <button
                    ref={zoomInButtonRef}
                    className="custom-zoom-button inc"
                    onClick={() => map.zoomIn()}
                >
                    <AddIcon />
                </button>
            </CustomTooltip>

            <CustomTooltip title={t("tooltips.controls.map.zoomOut")} placement="left">
                <button
                    ref={zoomOutButtonRef}
                    className="custom-zoom-button dec"
                    onClick={() => map.zoomOut()}
                >
                    <RemoveIcon />
                </button>
            </CustomTooltip>
        </div>
    );
}

export default CustomZoomControl;

/** End of file CustomZoomControl.tsx */
