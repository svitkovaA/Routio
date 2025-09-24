/**
 * @file Layers.tsx
 * @brief Provides map layers and satellite overlay data
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";

export const useLayers = () => {
    const { t } = useTranslation();

    const baseLayers = [
        {
            name: t("map.standartMap"),
            url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution: t("map.attribution")
        },
        {
            name: t("map.cycleMap"),
            url: "https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png",
            attribution: t("map.attributionCycle")
        },
        {
            name: t("map.satelliteMap"),
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution: t("map.attributionSatellite")
        }
    ]

    const satelliteOverlay =
        { 
            name: t("map.satelliteOverlay"),
            url: "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}", 
            attribution: t("map.attributionSatellite"), 
        }

    return { baseLayers, satelliteOverlay };
};

/** End of file Layers.tsx */
