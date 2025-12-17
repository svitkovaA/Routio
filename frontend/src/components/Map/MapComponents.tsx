import L from "leaflet";
import { useMapEvent } from "react-leaflet";


export function createPinIcon(label: string, translatedLabel?: string) {
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

export function SetViewOnClick({ onMapClick }: { onMapClick: (lat: number, lng: number) => boolean }) {
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
