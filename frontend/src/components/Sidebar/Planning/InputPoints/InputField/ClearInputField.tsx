/**
 * @file ClearInputField.tsx
 * @brief Displays component with an icon for clearing the input field
 * @author Andrea Svitkova (xsvitka00)
 */

import InputAdornment from "@mui/material/InputAdornment";
import ClearIcon from '@mui/icons-material/Clear';
import { IconButton } from "@mui/material";
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";

type ClearInputFieldProps = {
    clearWaypoint: () => void;
    render: boolean;
};

function ClearInputField({ 
    clearWaypoint,
    render
} : ClearInputFieldProps) {
    const { t } = useTranslation();
    
    if (!render) 
        return null;
    
    return (
        <CustomTooltip title={t("tooltips.inputForm.clearField")}>
            <InputAdornment position="end">
                <IconButton
                    aria-label="Clear field"
                    onClick={() => clearWaypoint()}
                    size="small"
                    edge="end"
                    onMouseDown={(e) => e.preventDefault()}
                    sx={{ mr: -1, color: 'var(--color-icons)' }}
                    tabIndex={-1}
                >
                    <ClearIcon />
                </IconButton>
            </InputAdornment>
        </CustomTooltip>
    );
}

export default ClearInputField;

/* End of file ClearInputField.tsx */
