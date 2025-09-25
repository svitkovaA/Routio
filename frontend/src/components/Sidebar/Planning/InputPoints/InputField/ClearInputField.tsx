/**
 * @file ClearInputField.tsx
 * @brief Displays component with an icon for clearing the input field
 * @author Andrea Svitkova (xsvitka00)
 */

import InputAdornment from "@mui/material/InputAdornment";
import { IconButton } from "@mui/material";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark } from '@fortawesome/free-solid-svg-icons';

type ClearInputFieldProps = {
    clearWaypoint: () => void;
    render: boolean;
};

function ClearInputField({ 
    clearWaypoint,
    render
} : ClearInputFieldProps) {
    if (!render) return null;
    
    return (
        <InputAdornment position="end">
            <IconButton
                aria-label="Clear field"
                onClick={() => clearWaypoint()}
                size="small"
                edge="end"
                onMouseDown={(e) => e.preventDefault()}
                sx={{ mr: -1 }}
                tabIndex={-1}
            >
                <FontAwesomeIcon icon={faXmark} />
            </IconButton>
        </InputAdornment>
    );
}

export default ClearInputField;

/* End of file ClearInputField.tsx */
