/**
 * @file leaflet-markercluster.d.ts
 * @brief Type declaration for marker cluster component
 * @author Andrea Svitkova (xsvitka00)
 */

declare module "leaflet.markercluster" {
    import * as L from "leaflet";

    export class MarkerCluster extends L.Marker {
        getChildCount(): number;
        getAllChildMarkers(): L.Marker[];
        zoomToBounds(): void;
    }

    export interface MarkerClusterGroupOptions extends L.LayerOptions {
        chunkedLoading?: boolean;
        zoomToBoundsOnClick?: boolean;
        showCoverageOnHover?: boolean;
        iconCreateFunction?: (cluster: MarkerCluster) => L.Icon | L.DivIcon;
    }
}

/** End of file leaflet-markercluster.d.ts */