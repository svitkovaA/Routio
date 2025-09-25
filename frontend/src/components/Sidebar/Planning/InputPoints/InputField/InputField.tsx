/**
 * @file InputField.tsx
 * @brief Displays input field component for entering waypoints in the planning form
 * @author Andrea Svitkova (xsvitka00)
 */

import { memo } from "react";
import TextField from "@mui/material/TextField";
import { useTranslation } from "react-i18next";
import { InputText, Waypoint } from "../../../../types/types";
import LocationDot from "./LocationDot";
import ClearInputField from "./ClearInputField";
import RemoveInputField from "./RemoveInputField";
import "./InputField.css";

type InputFieldProps = {
    index: number;
    lastIndex: number;
    waypoint: Waypoint;
    waypointsLength: number;
    handleWaypointChange: (index: number, value: string) => void;
    activeField: number | null;
    setActiveField: (index: number | null) => void;
    handleKeyDown: (e: React.KeyboardEvent<HTMLDivElement>, index: number) => void;
    setSuggestions: (value: InputText[]) => void;
    clearWaypoint: (index: number, clearDisplayName: boolean) => void;
    removeWaypoint: (index: number) => void;
    setMapSelectionIndex: (value: number) => void;
    closeSidebar: () => void;
}

function InputField({
    index,
    lastIndex,
    waypoint,
    waypointsLength,
    handleWaypointChange,
    activeField,
    setActiveField,
    handleKeyDown,
    setSuggestions,
    clearWaypoint,
    removeWaypoint,
    setMapSelectionIndex,
    closeSidebar,
} : InputFieldProps) {
    const { t } = useTranslation();
    const label = () => {
        if (index === 0) {
            return t("planning.origin");
        }
        if (index === lastIndex) {
            return t("planning.destination");
        }
        return t("planning.intermediatePoint", {index});
    };

    const placeHolder = () => {
        if (index === 0) {
            return t("planning.setOrigin");
        }
        if (index === lastIndex) {
            return t("planning.setDestination");
        }
        return t("planning.setIntermediatePoint");
    };

    return (
        <TextField
            required
            label={label()}
            placeholder={placeHolder()}
            value={waypoint.displayName}
            onChange={(e) => handleWaypointChange(index, e.target.value)}
            onFocus={() => setActiveField(index)}
            onBlur={() => {
              setActiveField(null);
              setSuggestions([]);
            }}
            onKeyDown={(e) => handleKeyDown(e, index)}
            fullWidth
            className="input-field"
            autoComplete="off"
            slotProps={{
              inputLabel: { shrink: true },
              input: {
                endAdornment: (
                  <>
                    <ClearInputField 
                        clearWaypoint={() => clearWaypoint(index, true)}
                        render={index === activeField && waypoint.displayName.length > 0}
                    />
                    
                    <LocationDot 
                        onClick={() => {
                            setMapSelectionIndex(index);
                            if (window.innerWidth < 769) closeSidebar();
                        }}
                    />

                    <RemoveInputField 
                        onClick={() => removeWaypoint(index)}
                        render={waypointsLength > 2}
                    />
                  </>
                )
              },
            }}
        />
    );
}

export default memo(InputField);

/* End of file InputField.tsx */
