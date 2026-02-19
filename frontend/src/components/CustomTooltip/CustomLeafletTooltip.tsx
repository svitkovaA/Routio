/**
 * @file CustomLeafletTooltip.tsx
 * @brief Custom Leaflet tooltip for map components
 * @author Andrea Svitkova (xsvitka00)
 */

import { Tooltip as LeafletTooltip } from "react-leaflet";
import { ReactNode } from "react";
import "./CustomLeafletTooltip.css"

type Props = {
    children: ReactNode;
    direction?: "top" | "bottom" | "left" | "right";
};

function CustomLeafletTooltip({
    children,
    direction = "top"
} : Props) {

    return (
        <LeafletTooltip
            sticky={false}
            interactive={false}
            direction={direction}
            opacity={0}
            className="routio-leaflet-tooltip"
        >
            {children}
        </LeafletTooltip>
    );
}

export default CustomLeafletTooltip;

/** End of file CustomLeafletTooltip.tsx */
