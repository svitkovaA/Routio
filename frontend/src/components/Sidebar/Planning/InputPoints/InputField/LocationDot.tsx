/**
 * @file LocationDot.tsx
 * @brief Displays location icon for getting location from the map
 * @author Andrea Svitkova (xsvitka00)
 */

import InputAdornment from "@mui/material/InputAdornment";
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { IconButton } from "@mui/material";
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";

type LocationDotProps = {
    onClick: () => void;
}

function LocationDot({
    onClick
} : LocationDotProps) {
    const { t } = useTranslation();

    return (
        <CustomTooltip title={t("tooltips.inputForm.mapSelect")}>
            <InputAdornment position="end">
                <IconButton
                    aria-label="Position from map"
                    onClick={onClick}
                    size="small"
                    edge="end"
                    sx={{mr: -1, color: 'var(--color-icons)'}}
                    tabIndex={-1}
                >
                    <LocationOnIcon />
                </IconButton>
            </InputAdornment>
        </CustomTooltip>
    );
}

export default LocationDot;

/* End of file LocationDot.tsx */
