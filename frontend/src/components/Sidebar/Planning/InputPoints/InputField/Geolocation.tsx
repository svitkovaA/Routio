/**
 * @file Geolocation.tsx
 * @brief Component with an icon for detecting current user position
 * @author Andrea Svitkova (xsvitka00)
 */

import InputAdornment from "@mui/material/InputAdornment";
import MyLocationIcon from "@mui/icons-material/MyLocation";
import { IconButton } from "@mui/material";
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";

type GeolocationProps = {
    onClick: () => void;    // Callback that handles current user position selection
    render: boolean;        // Determines whether the position detection button should be rendered
}

function Geolocation({
    onClick,
    render
}: GeolocationProps) {
    // Translation function
    const { t } = useTranslation();

    // Do not render the component if rendering is disabled
    if (!render) {
        return null;
    }

    return (
        <CustomTooltip title={t("tooltips.inputForm.currentPosition")}>
            <InputAdornment position="end">
                <IconButton
                    aria-label="Current location"
                    onClick={onClick}
                    size="small"
                    edge="end"
                    sx={{ mr: -1, color: "var(--color-icons)" }}
                    tabIndex={-1}
                >
                    <MyLocationIcon />
                </IconButton>
            </InputAdornment>
        </CustomTooltip>
    );
}

export default Geolocation;

/** End of file Geolocation.tsx */
