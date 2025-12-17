/**
 * @file Options.tsx
 * @brief Displays dropdown menus for selecting options in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import MenuItem from '@mui/material/MenuItem';
import { TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import { RoutePreference } from "../../../types/types";
import { useInput } from '../../../InputContext';

function Options() {
    const { t } = useTranslation();

    const {
        preference, setPreference,
        useOwnBike, setUseOwnBike
    } = useInput();

    return (
        <div className="grid-wrapper">
            <TextField
                select
                label={t("planning.routePreferences")}
                value={preference}
                variant="outlined"
                onChange={(event) => {
                    setPreference(event.target.value as RoutePreference);
                }}
                slotProps={{
                    inputLabel: { shrink: true },
                }}
            >
                <MenuItem value={"fastest"}>{t("planning.routePreference.fastestRoute")}</MenuItem>
                <MenuItem value={"shortest"}>{t("planning.routePreference.shortestRoute")}</MenuItem>
                <MenuItem value={"transfers"}>{t("planning.routePreference.minimizeTransfers")}</MenuItem>
            </TextField>
            
            <TextField
                select
                label={t("planning.bikeOptions")}
                value={useOwnBike.toString()}
                variant="outlined"
                onChange={(event) => {
                    setUseOwnBike(event.target.value === "true");
                }}
                slotProps={{
                    inputLabel: { shrink: true },
                }}
            >
                <MenuItem value="true">{t("planning.bikeOption.ownBike")}</MenuItem>
                <MenuItem value="false">{t("planning.bikeOption.sharedBike")}</MenuItem>
            </TextField>
        </div>
    );
}

export default Options;

/** End of file Options.tsx */
