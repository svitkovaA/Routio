/**
 * @file RemoveInputField.tsx
 * @brief Component with an icon for removing the input field
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import { IconButton } from "@mui/material";
import InputAdornment from "@mui/material/InputAdornment";
import DeleteIcon from '@mui/icons-material/Delete';
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";

type RemoveInputFieldProps = {
    onClick: () => void;        // Callback that removes the waypoint data
    render: boolean;            // Determines whether the remove button should be rendered
}

function RemoveInputField({
    onClick,
    render
} : RemoveInputFieldProps) {
    // Translation function
    const { t } = useTranslation();

    // Do not render the component if rendering is disabled
    if (!render) 
        return null;
    
    return (
        <CustomTooltip title={t("tooltips.inputForm.removeWaypoint")}>
            <InputAdornment position="end">
                <IconButton
                    aria-label="Remove waypoint"
                    onClick={onClick}
                    size="small"
                    edge="end"
                    sx={{ color: 'var(--color-icons)' }}
                    tabIndex={-1}
                >
                    <DeleteIcon />
                </IconButton>
            </InputAdornment>
        </CustomTooltip>
    );
}

export default RemoveInputField;

/* End of file RemoveInputField.tsx */
