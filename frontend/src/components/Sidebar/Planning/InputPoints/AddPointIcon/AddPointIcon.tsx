/**
 * @file AddPointIcon.tsx
 * @brief Displays icon for displaying an intermediate point, and vertical line
 * @author Andrea Svitkova (xsvitka00)
 */

import { IconButton } from "@mui/material";
import AddBoxIcon from '@mui/icons-material/AddBox';
import './AddPointIcon.css'
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";

type AddPointIconProps = {
    onClick: () => void;
    render: boolean;
    disabled: boolean;
}

function AddPointIcon({
    onClick,
    render,
    disabled
} : AddPointIconProps) {
    const { t } = useTranslation();

    if (!render) 
        return null;

    return (
        <div className="line">
            <CustomTooltip title={t("tooltips.inputForm.addWaypoint")}>
                <IconButton
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
