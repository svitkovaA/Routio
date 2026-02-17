/**
 * @file CustomTooltip.tsx
 * @brief 
 * @author Andrea Svitkova (xsvitka00)
 */

import { ReactElement, ReactNode } from "react";
import Tooltip from "@mui/material/Tooltip";

type CustomTooltipProps = {
    title: ReactNode;                                   // Tooltip content
    children: ReactElement;                             // Wrapped element
    placement?: "top" | "bottom" | "left" | "right";    // Tooltip position
};

function CustomTooltip({
    title,
    children,
    placement = "top"
}: CustomTooltipProps) {
    return (
        <Tooltip
            title={title}
            arrow
            placement={placement}
            enterDelay={800}
            slotProps={{
                popper: {
                    modifiers: [
                        {
                            name: "offset",
                            options: {
                                offset: [0, -7],
                            },
                        },
                    ],
                },
                tooltip: {
                    sx: {
                        color: "#fff",
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
