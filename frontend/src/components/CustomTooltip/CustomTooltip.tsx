/**
 * @file CustomTooltip.tsx
 * @brief Custom MUI tooltip for application components
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState, useEffect } from "react";
import type { ReactElement, ReactNode } from "react";
import Tooltip from "@mui/material/Tooltip";

type CustomTooltipProps = {
    title: ReactNode;                                   // Tooltip content
    children: ReactElement;                             // Wrapped element
    disableTooltip?: boolean;                           // Conditionally disable tooltip
    placement?: "top" | "bottom" | "left" | "right";    // Tooltip position
};

function CustomTooltip({
    title,
    children,
    disableTooltip = false,
    placement = "top"
}: CustomTooltipProps) {

    const [tooltipOpen, setTooltipOpen] = useState(false);

    useEffect(() => {
        if (disableTooltip) {
            setTooltipOpen(false);
        }
    }, [disableTooltip]);

    return (
        <Tooltip
            title={title}
            arrow
            placement={placement}
            open={!disableTooltip && tooltipOpen}
            onOpen={() => {
                if (!disableTooltip) {
                    setTooltipOpen(true);
                }
            }}
            onClose={() => setTooltipOpen(false)}
            enterDelay={800}
            enterNextDelay={800}
            leaveDelay={100}
            slotProps={{
                popper: {
                    sx: {
                        zIndex: 1200
                    },
                    modifiers: [
                        {
                            name: "offset",
                            options: {
                                offset: [0, -7]
                            },
                        },
                    ],
                },
                tooltip: {
                    sx: {
                        color: "var(--color-white-text)",
                        fontSize: "12px",
                    },
                }
            }}
        >
            {children}
        </Tooltip>
    );
}

export default CustomTooltip;

/** End of file CustomTooltip.tsx */
