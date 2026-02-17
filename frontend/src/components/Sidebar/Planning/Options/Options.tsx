/**
 * @file Options.tsx
 * @brief Displays dropdown menus for selecting routing preferences and bicycle usage options
 * @author Andrea Svitkova (xsvitka00)
 */

import MenuItem from '@mui/material/MenuItem';
import { useTranslation } from "react-i18next";
import { RoutePreference } from "../../../types/types";
import { useInput } from '../../../InputContext';
import OptionSelect from './OptionSelect';

/**
 * Returns next value in a circular array
 * 
 * @template T Generic type of array elements
 * @param array Array of available options
 * @param current Currently selected value
 * @param direction  direction +1 for next, -1 for previous
 * @returns Next value in circular order
 */
function getNextValue<T>(array: T[], current: T, direction: number): T {
    const index = array.indexOf(current);
    return array[(index + direction + array.length) % array.length];
}

function Options() {
    // Translation function
    const { t } = useTranslation();

    // User input context
    const {
        preference, setPreference,
        useOwnBike, setUseOwnBike
    } = useInput();

    // Available route optimization options
    const routePreferences: RoutePreference[] = [
        "fastest",
        "shortest",
        "transfers"
    ];
    
    // Available bicycle usage options
    const bikeOptions = [true, false];

    return (
        <div className="grid-wrapper">
            {/* Route optimization selection */}
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

            {/* Bicycle usage selection */}
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
