/**
 * @file DetailButton.tsx
 * @brief Button component for showing detailed information about the trip
 * @author Andrea Svitkova (xsvitka00)
 */

import { IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";

function DetailButton() {
    // Translation function
    const { t } = useTranslation();

    return (
        <IconButton>
            {t("resultsInfo.detail")}
        </IconButton>
    );
}

export default DetailButton;

/** End of file DetailButton.tx */
