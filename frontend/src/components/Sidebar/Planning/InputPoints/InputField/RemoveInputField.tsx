/**
 * @file RemoveInputField.tsx
 * @brief Display component with an icon for deleting the input field
 * @author Andrea Svitkova (xsvitka00)
 */

import { IconButton } from "@mui/material";
import InputAdornment from "@mui/material/InputAdornment";
import DeleteIcon from '@mui/icons-material/Delete';
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";

type RemoveInputFieldProps = {
    onClick: () => void;
    render: boolean;
}

function RemoveInputField({
    onClick,
    render
} : RemoveInputFieldProps) {
    const { t } = useTranslation();

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
