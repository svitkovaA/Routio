/**
 * @file Section.tsx
 * @brief Reusable component for settings configuration
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import TextField from "@mui/material/TextField";
import CustomTooltip from '../../../../CustomTooltip/CustomTooltip';
import { useNotification } from "../../../../Contexts/NotificationContext";
import "./Section.css";

type SectionProps = {
    label: string;                                                  // Label for the input field
    value: number;                                                  // Current value
    setValue: (value: number | ((prev: number) => number)) => void; // Setter for updating the value
    bounds: { min: number, max: number };                           // Minimum and maximum allowed value
}

function Section({
    label,
    value,
    setValue,
    bounds
} : SectionProps) {
    //Translation function
    const { t } = useTranslation();

    // Stores the temporary raw string representation of the input value
    const [rawValue, setRawValue] = useState<string>(value.toString());

    // Notification context
    const { showNotification } = useNotification();

    /**
     * Handles manual input value change
     * 
     * @param e Change event from the input filed
     */
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;

        // Allow empty string temporarily
        if (value === "") {
            setRawValue("");
            return;
        }

        // Reject non numeric input or long values
        if (!/^\d+$/.test(value) || value.length > 3){
            return;
        }

        // Remove leading zero if more than one digit
        const cleaned = (value.startsWith("0") && value.length > 1) ? value.substring(1) : value;

        // Update local raw state and validated numeric state
        setRawValue(cleaned);
        setValue(Number(cleaned));
    };

    /**
     * Validates and clamps the value on blur
     */
    const validate = () => {
        // If input left empty, reset to minimum bound
        if (rawValue === "") {
            setRawValue(bounds.min.toString());
            setValue(bounds.min);
            return;
        }

        // Convert input string to numeric value
        const numericValue = Number(rawValue);

        // Clamp value within defined bounds
        const clampedValue = Math.max(bounds.min, Math.min(bounds.max, numericValue));

        // Show warning notification if the value was clamped
        if (numericValue !== clampedValue) {
            showNotification(t("warnings.valueClamp"), "warning");
        }

        // Update state with the clamped value
        setRawValue(clampedValue.toString());
        setValue(clampedValue);
    };

    /**
     * Handles keyboard interactions for the numeric input field
     * 
     * @param e Keyboard event
     */
    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "Enter") {
            e.preventDefault();
            validate();
            (e.target as HTMLInputElement).blur();
        }
        if (e.key === "ArrowUp") {
            e.preventDefault();
            const newValue = Math.min(bounds.max, value + 1);
            setValue(newValue);
            setRawValue(newValue.toString());
        }

        if (e.key === "ArrowDown") {
            e.preventDefault();
            const newValue = Math.max(bounds.min, value - 1);
            setValue(newValue);
            setRawValue(newValue.toString());
        }
    };

    // Reference to interval
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    /**
     * Starts continuous value change if button pressed
     * 
     * @param direction Direction the value is changed
     */
    const startChanging = (direction: "inc" | "dec") => {
        // Apply first step immediately
        setValue(prev => {
            const newValue =
                direction === "inc"
                    ? Math.min(bounds.max, prev + 1)
                    : Math.max(bounds.min, prev - 1);

            setRawValue(newValue.toString());
            return newValue;
        });

        // Start interval to repeatedly update value while holding
        intervalRef.current = setInterval(() => {
            setValue(prev => {
                const newValue =
                    direction === "inc"
                        ? Math.min(bounds.max, prev + 1)
                        : Math.max(bounds.min, prev - 1);

                setRawValue(newValue.toString());
                return newValue;
            });
        }, 100);
    };

    /**
     * Stops continuous value change when button is released
     */
    const stopChanging = () => {
        // Clear interval if active
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    };

    return(
        <div className="section">
            <span className="section-label">
                {label}
            </span>
            <TextField
                type="text"
                inputMode="numeric"
                value={rawValue}
                onChange={handleChange}
                onBlur={validate}
                onKeyDown={handleKeyDown}
                className="number-input"
                autoComplete="off"
                slotProps={{
                    htmlInput: {
                        autoComplete: "off",
                        ...bounds,
                        step: 1,
                    },
                    input: {
                        sx: {
                            '& input[type=number]': {
                                MozAppearance: 'textfield', // Firefox
                            },
                            '& input[type=number]::-webkit-outer-spin-button': {
                                WebkitAppearance: 'none',
                                margin: 0,
                            },
                            '& input[type=number]::-webkit-inner-spin-button': {
                                WebkitAppearance: 'none',
                                margin: 0,
                            },
                        },
                        endAdornment: (
                            <InputAdornment 
                                position="end" 
                                className="settings-adornment"
                            >

                                {/* Decrease value button */}
                                <CustomTooltip
                                    title={t("tooltips.settings.decrease")}
                                >
                                    <IconButton
                                        onMouseDown={() => startChanging("dec")}
                                        onMouseUp={stopChanging}
                                        onMouseLeave={stopChanging}
                                        onTouchStart={() => startChanging("dec")}
                                        onTouchEnd={stopChanging}
                                        size="small"
                                        disabled={value === bounds.min}
                                    >
                                        <RemoveIcon fontSize="small" />
                                    </IconButton>
                                </CustomTooltip>

                                {/* Increase value button */}
                                <CustomTooltip
                                    title={t("tooltips.settings.increase")}
                                >
                                    <IconButton
                                        onMouseDown={() => startChanging("inc")}
                                        onMouseUp={stopChanging}
                                        onMouseLeave={stopChanging}
                                        onTouchStart={() => startChanging("inc")}
                                        onTouchEnd={stopChanging}
                                        size="small"
                                        disabled={value === bounds.max}
                                    >
                                        <AddIcon fontSize="small" />
                                    </IconButton>
                                </CustomTooltip>
                            </InputAdornment>
                        ),
                    },
                }}
            />
        </div>
    );
}

export default Section;

/** End of file Section.tsx */
