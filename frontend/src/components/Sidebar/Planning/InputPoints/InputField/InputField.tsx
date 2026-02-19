/**
 * @file InputField.tsx
 * @brief Input field component for waypoint entry in the planning form
 * @author Andrea Svitkova (xsvitka00)
 */

import { memo, useRef } from "react";
import { useTranslation } from "react-i18next";
import TextField from "@mui/material/TextField";
import { InputText, Waypoint } from "../../../../types/types";
import LocationDot from "./LocationDot";
import ClearInputField from "./ClearInputField";
import RemoveInputField from "./RemoveInputField";
import { useInput } from "../../../../InputContext";
import "./InputField.css";

type InputFieldProps = {
    index: number;                                  // Index of waypoint in array
    lastIndex: number;                              // Index of last waypoint, destination
    waypoint: Waypoint;                             // Current waypoint object
    waypointsLength: number;                        // Total number of waypoints
    handleWaypointChange: (
        index: number,
        value: string
    ) => void;                                      // Handler for input value change
    handleKeyDown: (
        e: React.KeyboardEvent<HTMLDivElement>,
        index: number
    ) => void;                                      // Keyboard navigation handler
    suggestions: InputText[];                       // Current suggestion list
    setSuggestions: (value: InputText[]) => void;   // Setter for suggestions
    highlightedIndex: number;                       // Currently highlighted suggestion index
    resetHighlightedIndex: () => void;              // Reset highlight state
    closeSidebar: () => void;                       // Closes sidebar
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
    // Translation function
    const { t } = useTranslation();

    // Reference to the underlying input element
    const inputRef = useRef<HTMLInputElement | null>(null);

    // User input context
    const {
        activeField, setActiveField,
        clearWaypoint,
        removeWaypoint,
        setMapSelectionIndex,
        setWaypoints,
        fieldErrors, setFieldErrors
    } = useInput();

    // Returns label based on waypoint position
    const label = () => {
        if (index === 0) {
            return t("planning.origin");
        }
        if (index === lastIndex) {
            return t("planning.destination");
        }
        return t("planning.intermediatePoint", {index});
    };

    // Returns placeholder text based on waypoint position
    const placeHolder = () => {
        if (index === 0) {
            return t("planning.setOrigin");
        }
        if (index === lastIndex) {
            return t("planning.setDestination");
        }
        return t("planning.setIntermediatePoint");
    };

    // Indicates whether target field is focused
    const isFocused = activeField === index;

    // Indicate whether required error occurred
    const isRequiredError = !isFocused && fieldErrors.includes(index);

    // Indicate whether required error occurred
    const isInvalidAddress = !isFocused && waypoint.displayName.trim() !== "" && (waypoint.lat === 0 || waypoint.lon === 0);

    return (
        <TextField
            required
            error={isRequiredError || isInvalidAddress}
            helperText={
                isRequiredError ? t("planning.fieldRequired") : isInvalidAddress ? t("planning.invalidAddress") : ""
            }
            label={label()}
            placeholder={placeHolder()}
            value={waypoint.displayName}
            sx={{
                position: "relative",

                "& .MuiFormHelperText-root": {
                position: "absolute",
                bottom: "-18px",
                right: 0,
                margin: 0
                },
            }}
            onChange={(e) => {
                const value = e.target.value;

                // Update waypoint input value
                handleWaypointChange(index, value);

                // Clear validation error
                if (fieldErrors.includes(index)) {
                    setFieldErrors(prev => prev.filter(i => i !== index));
                }
            }}
            onFocus={() => setActiveField(index)}
            onBlur={() => {
                // Clear validation error
                if (fieldErrors.includes(index)) {
                    setFieldErrors(prev => prev.filter(i => i !== index));
                }
                // Attempt to apply the selected or first suggestion
                if (!waypoint.isActive) {
                    const suggestionIndex = highlightedIndex >= 0 ? highlightedIndex : 0;
                    const suggestion = suggestions[suggestionIndex];
                    setWaypoints(prev => {
                        // No suggestion selected
                        if (!suggestion) {
                            prev[index] = {
                                ...prev[index],
                                isPreview: false,
                                lat: 0,
                                lon: 0
                            }
                        }
                        // Apply selected suggestion
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
