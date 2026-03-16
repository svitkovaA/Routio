/**
 * @file AddPointIcon.tsx
 * @brief Renders an icon for adding an intermediate waypoint, including a vertical connector line
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import { IconButton } from "@mui/material";
import AddBoxIcon from '@mui/icons-material/AddBox';
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import './AddPointIcon.css'

type AddPointIconProps = {
    onClick: () => void;        // Callback triggered when the add icon is clicked
    render: boolean;            // Determines whether the component should be rendered
    disabled: boolean;          // Disables the button when adding a waypoint is not allowed
}

function AddPointIcon({
    onClick,
    render,
    disabled
} : AddPointIconProps) {
    // Translation function
    const { t } = useTranslation();

    // Do not render the component if adding waypoints is not allowed
    if (!render) 
        return null;

    return (
        <div className="line">
            <CustomTooltip title={t("tooltips.inputForm.addWaypoint")}>
                <IconButton
                    className="add-point-icon"
                    aria-label="Add intermediate waypoint"
                    onClick={onClick}
                    size="small"
                    sx={{ marginBottom: 1, color: 'var(--color-icons)' }}
                    tabIndex={-1}
                    disabled={disabled}
                >
                    <AddBoxIcon/>
                </IconButton>
            </CustomTooltip>
        </div>
    );
}

export default AddPointIcon;

/* End of file AddPointIcon.tsx */
