/**
 * @file RemoveInputField.tsx
 * @brief Display component with an icon for deleting the input field
 * @author Andrea Svitkova (xsvitka00)
 */

import { IconButton } from "@mui/material";
import InputAdornment from "@mui/material/InputAdornment";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash } from '@fortawesome/free-solid-svg-icons';

type RemoveInputFieldProps = {
    onClick: () => void;
    render: boolean;
}

function RemoveInputField({
    onClick,
    render
} : RemoveInputFieldProps) {
    if (!render) 
        return null;
    
    return (
        <InputAdornment position="end">
            <IconButton
                aria-label="Remove waypoint"
                onClick={onClick}
                size="small"
                edge="end"
                tabIndex={-1}
            >
                <FontAwesomeIcon icon={faTrash} />
            </IconButton>
        </InputAdornment>
    );
}

export default RemoveInputField;

/* End of file RemoveInputField.tsx */
