/**
 * @file Options.tsx
 * @brief Displays dropdown menus for selecting options in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import MenuItem from '@mui/material/MenuItem';
import { useTranslation } from "react-i18next";
import { RoutePreference } from "../../../types/types";
import { useInput } from '../../../InputContext';
import OptionSelect from './OptionSelect';

function getNextValue<T>(array: T[], current: T, direction: number): T {
    const index = array.indexOf(current);
    return array[(index + direction + array.length) % array.length];
}

function Options() {
    const { t } = useTranslation();

    const {
        preference, setPreference,
        useOwnBike, setUseOwnBike
    } = useInput();

    const routePreferences: RoutePreference[] = [
        "fastest",
        "shortest",
        "transfers"
    ];

    const bikeOptions = [true, false];

    return (
        <div className="grid-wrapper">
            {/* Route preferences */}
            <OptionSelect
                label={t("planning.routePreferences")}
                value={preference}
                onChange={(event) => {
                    setPreference(event.target.value as RoutePreference);
                }}
                setOption={(direction: number) => setPreference(
                    getNextValue(routePreferences, preference, direction)
                )}
            >
                <MenuItem value={"fastest"}>
                    {t("planning.routePreference.fastestRoute")}
                </MenuItem>
                <MenuItem value={"shortest"}>
                    {t("planning.routePreference.shortestRoute")}
                </MenuItem>
                <MenuItem value={"transfers"}>
                    {t("planning.routePreference.minimizeTransfers")}
                </MenuItem>
            </OptionSelect>

            {/* Bicycle preferences */}
            <OptionSelect
                label={t("planning.bikeOptions")}
                value={useOwnBike.toString()}
                onChange={(event) => {
                    setUseOwnBike(event.target.value === "true");
                }}
                setOption={(direction: number) => setUseOwnBike(
                    getNextValue(bikeOptions, useOwnBike, direction)
                )}
            >
                <MenuItem value="true">
                    {t("planning.bikeOption.ownBike")}
                </MenuItem>
                <MenuItem value="false">
                    {t("planning.bikeOption.sharedBike")}
                </MenuItem>
            </OptionSelect>
        </div>
    );
}

export default Options;

/** End of file Options.tsx */
