/**
 * @file InputField.tsx
 * @brief Input field component for waypoint entry in the planning form
 * @author Andrea Svitkova (xsvitka00)
 */

import { memo, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import TextField from "@mui/material/TextField";
import { InputText, Waypoint } from "../../../../types/types";
import LocationDot from "./LocationDot";
import ClearInputField from "./ClearInputField";
import RemoveInputField from "./RemoveInputField";
import Geolocation from "./Geolocation";
import { useInput } from "../../../../Contexts/InputContext";
import { useNotification } from "../../../../Contexts/NotificationContext";
import { NW_LAT, NW_LON, SE_LAT, SE_LON } from "../../../../config/config";
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

/**
 * Parses provided coordinates
 * 
 * @param input Provided coordinates
 * @returns Parsed coordinates
 */
function parseCoordinates(input: string) {
    const parts = input.split(/[,;\s]+/);
    const lat = parseFloat(parts[0]);
    const lon = parseFloat(parts[1]);

    if (lat >= SE_LAT && lat <= NW_LAT && lon >= NW_LON && lon <= SE_LON) {
        return { lat, lon };
    }

    return null;
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
    const { t, i18n } = useTranslation();

    // Reference to the underlying input element
    const inputRef = useRef<HTMLInputElement | null>(null);

    // User input context
    const {
        activeField, setActiveField,
        clearWaypoint,
        removeWaypoint,
        mapSelectionIndex, setMapSelectionIndex,
        setWaypoints,
        fieldErrors, setFieldErrors,
        waypoints
    } = useInput();

    // Notification context
    const { showNotification } = useNotification();

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

    // Stores the previously active language
    const previousLanguage = useRef(i18n.language);

    /**
     *  User location handle
     */
    useEffect(() => {
        // Language before the change
        const oldLanguage = previousLanguage.current;

        // Update waypoints after language change
        setWaypoints(prev => {
            const updated = [...prev];

            // Rerender string when language changes
            updated.forEach((wp, i) => {
                if (wp.displayName === t("planning.position", { lng: oldLanguage })) {
                    updated[i] = {
                        ...wp,
                        displayName: t("planning.position")
                    };
                }
            });

            return updated;
        });

        // Store current language for the next change detection
        previousLanguage.current = i18n.language;
    }, [i18n.language, setWaypoints, t]);

    // Detects the users current geographic position
    const detectCurrentPosition = () => {
        // Check if the browser supports the Geolocation API
        if (!navigator.geolocation) {
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                // Extract latitude and longitude from the detected position
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                // Update the waypoint list
                setWaypoints(prev => {
                    const updated = [...prev];

                    updated[index] = {
                        ...updated[index],
                        isPreview: false,
                        isActive: true,
                        displayName: t("planning.position"),
                        lat,
                        lon,
                        bikeStationId: null,
                        origin: null
                    };

                    return updated;
                });
            },
            () => {
                // If location detection fails
                showNotification(t("errors.positionDetectionFailed"), "error");
            },
            {
                enableHighAccuracy: true
            }
        );
    };

    // Updates error on coordinates change
    useEffect(() => {
        if (waypoint.lat !== 0 && waypoint.lon !== 0) {
            setFieldErrors(prev => prev.filter(i => i !== index));
        }
    }, [waypoint.lat, waypoint.lon, index, setFieldErrors]);

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
                zIndex: 1,
                backgroundColor: "var(--color-background)",
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
                            // Regex for coordinates
                            const coordsRegex = /^\s*-?\d+(\.\d+)?\s*[,;\s]\s*-?\d+(\.\d+)?\s*$/;

                            // Input field contains geographic coordinates
                            if (coordsRegex.test(waypoint.displayName)) {
                                const parsed = parseCoordinates(waypoint.displayName)
                                // Not possible to parse coordinates, set invalid field
                                if (!parsed) {
                                    prev[index] = {
                                        ...prev[index],
                                        isPreview: false,
                                        lat: 0,
                                        lon: 0,
                                        bikeStationId: null,
                                        origin: null
                                    }
                                }
                                // Possible to parse coordinates, set it as input
                                else {
                                    prev[index] = {
                                        ...prev[index],
                                        isPreview: false,
                                        isActive: true,
                                        displayName: `${parsed.lat.toFixed(5)}, ${parsed.lon.toFixed(5)}`,
                                        lat: parsed.lat,
                                        lon: parsed.lon,
                                        bikeStationId: null,
                                        origin: null
                                    }
                                }
                            }
                            // No matching regex, set invalid field
                            else {
                                prev[index] = {
                                    ...prev[index],
                                    isPreview: false,
                                    lat: 0,
                                    lon: 0,
                                    bikeStationId: null,
                                    origin: null
                                }
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
                                lon: suggestion.lon,
                                bikeStationId: null,
                                origin: null
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

                        {index === 0 && !waypoints.some(w => w.displayName === t("planning.position")) && (
                            <Geolocation
                                onClick={detectCurrentPosition}
                                render={index !== activeField || waypoint.displayName.length <= 0}
                            />
                        )}
                                            
                        <LocationDot
                            active={mapSelectionIndex === index}
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
