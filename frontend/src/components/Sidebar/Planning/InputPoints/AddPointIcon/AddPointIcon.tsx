/**
 * @file AddPointIcon.tsx
 * @brief Displays icon for displaying an intermediate point, and vertical line
 * @author Andrea Svitkova (xsvitka00)
 */

import { IconButton } from "@mui/material";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSquarePlus } from '@fortawesome/free-solid-svg-icons';
import './AddPointIcon.css'

type AddPointIconProps = {
    onClick: () => void;
    render: boolean;
}

function AddPointIcon({
    onClick,
    render
} : AddPointIconProps) {
    if (!render) 
        return null;

    return (
        <div className="line">
            <IconButton
                aria-label="Add intermediate waypoint"
                onClick={onClick}
                size="small"
                sx={{ marginBottom: 1 }}
                tabIndex={-1}
            >
                <FontAwesomeIcon icon={faSquarePlus}/>
            </IconButton>
        </div>
    );
}

export default AddPointIcon;

/* End of file AddPointIcon.tsx */
