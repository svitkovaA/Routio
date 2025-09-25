/**
 * @file LocationDot.tsx
 * @brief Displays location icon for getting location from the map
 * @author Andrea Svitkova (xsvitka00)
 */

import InputAdornment from "@mui/material/InputAdornment";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faLocationDot } from '@fortawesome/free-solid-svg-icons';
import { IconButton, SxProps } from "@mui/material";

type LocationDotProps = {
    onClick: () => void;
}

function LocationDot({
    onClick
} : LocationDotProps) {
    return (
        <InputAdornment position="end">
            <IconButton
                aria-label="Position from map"
                onClick={onClick}
                size="small"
                edge="end"
                sx={{mr: -1}}
                tabIndex={-1}
            >
                <FontAwesomeIcon icon={faLocationDot} />
            </IconButton>
        </InputAdornment>
    );
}

export default LocationDot;

/* End of file LocationDot.tsx */
