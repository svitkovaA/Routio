/**
 * @file InputField.tsx
 * @brief Displays input field component for entering waypoints in the planning form
 * @author Andrea Svitkova (xsvitka00)
 */

import { memo, useRef } from "react";
import TextField from "@mui/material/TextField";
import { useTranslation } from "react-i18next";
import { InputText, Waypoint } from "../../../../types/types";
import LocationDot from "./LocationDot";
import ClearInputField from "./ClearInputField";
import RemoveInputField from "./RemoveInputField";
import { useInput } from "../../../../InputContext";
import "./InputField.css";

type InputFieldProps = {
    index: number;
    lastIndex: number;
    waypoint: Waypoint;
    waypointsLength: number;
    handleWaypointChange: (index: number, value: string) => void;
    handleKeyDown: (e: React.KeyboardEvent<HTMLDivElement>, index: number) => void;
    suggestions: InputText[];
    setSuggestions: (value: InputText[]) => void;
    highlightedIndex: number;
    resetHighlightedIndex: () => void;
    closeSidebar: () => void;
}

function InputField({
    index,
    lastIndex,
    waypoint,
    waypointsLength,
    handleWaypointChange,
    handleKeyDown,
    suggestions,
    setSuggestions,
    highlightedIndex,
    resetHighlightedIndex,
    closeSidebar
} : InputFieldProps) {
    const { t } = useTranslation();

    const inputRef = useRef<HTMLInputElement | null>(null);

    const {
        activeField, setActiveField,
        clearWaypoint,
        removeWaypoint,
        setMapSelectionIndex,
        setWaypoints
    } = useInput();

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
                if (!waypoint.isActive) {
                    const suggestionIndex = highlightedIndex >= 0 ? highlightedIndex : 0;
                    const suggestion = suggestions[suggestionIndex];
                    setWaypoints(prev => {
                        if (!suggestion) {
                            prev[index] = {
                                ...prev[index],
                                isPreview: false,
                                displayName: "",
                                lat: 0,
                                lon: 0
                            }
                        }
                        else {
                            prev[index] = {
                                ...prev[index],
                                isPreview: false,
                                isActive: true,
                                displayName: [suggestion.name, suggestion.street, suggestion.city].filter(Boolean).join(", "),
                                lat: suggestion.lat,
                                lon: suggestion.lon
                            }
                        }
                        return prev;
                    });
                }
                setActiveField(null);
                setSuggestions([]);
                resetHighlightedIndex();
            }}
            onKeyDown={(e) => {
                handleKeyDown(e, index);
                if (e.key === "Enter")
                    inputRef.current?.blur();
            }}
            fullWidth
            className="input-field"
            autoComplete="off"
            slotProps={{
                inputLabel: { shrink: true },
                input: {
                    inputRef: inputRef,
                    endAdornment: (
                    <>
                        <ClearInputField 
                            clearWaypoint={() => clearWaypoint(index, true)}
                            render={index === activeField && waypoint.displayName.length > 0}
                        />
                        
                        <LocationDot 
                            onClick={() => {
                                setMapSelectionIndex(index);
                                if (window.innerWidth < 768) {
                                    closeSidebar();
                                }
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
