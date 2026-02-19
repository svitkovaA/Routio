/**
 * @file CustomZoomControl.tsx
 * @brief Custom zoom control component
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
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

    const map = useMap();
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!containerRef.current) {
            return;
        }

        L.DomEvent.disableClickPropagation(containerRef.current);
        L.DomEvent.disableScrollPropagation(containerRef.current);
    }, []);

    return (
        <div ref={containerRef} className="custom-zoom-control">
            <CustomTooltip title={t("tooltips.controls.map.zoomIn")} placement="left">
                <button
                    className="custom-zoom-button inc"
                    onClick={() => map.zoomIn()}
                >
                    <AddIcon />
                </button>
            </CustomTooltip>

            <CustomTooltip title={t("tooltips.controls.map.zoomOut")} placement="left">
                <button
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
