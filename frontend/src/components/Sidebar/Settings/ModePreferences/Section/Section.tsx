/**
 * @file Section.tsx
 * @brief Reusable component for settings configuration
 * @author Andrea Svitkova (xsvitka00)
 */

import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import TextField from "@mui/material/TextField";
import { useState } from 'react';
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

    /**
     * Handles manual input value change
     * 
     * @param e Change event from the input filed
     */
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;

        if (value === "") {
            setRawValue("");
            return;
        }

        if (!/^\d+$/.test(value) || value.length > 3){
            return;
        }

        const cleaned = (value.startsWith("0") && value.length > 1) ? value.substring(1) : value;

        setRawValue(cleaned);
        setValue(Number(cleaned));
    };

    const validate = () => {
        if (rawValue === "") {
            setRawValue(bounds.min.toString());
            setValue(bounds.min);
        }
        else {
            const newValue = Math.max(bounds.min, Math.min(bounds.max, Number(rawValue)));
            setRawValue(newValue.toString());
            setValue(newValue);
        }
    }

    const [rawValue, setRawValue] = useState<string>(value.toString());

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
                                <IconButton
                                    onClick={() => {
                                        const newValue = Math.max(bounds.min, value - 1);
                                        setValue(newValue);
                                        setRawValue(newValue.toString());
                                    }}
                                    size="small"
                                    disabled={value === bounds.min}
                                >
                                    <RemoveIcon fontSize="small" />
                                </IconButton>

                                {/* Increase value button */}
                                <IconButton
                                    onClick={() => {
                                        const newValue = Math.min(bounds.max, value + 1);
                                        setValue(newValue);
                                        setRawValue(newValue.toString());
                                    }}
                                    size="small"
                                    disabled={value === bounds.max}
                                >
                                    <AddIcon fontSize="small" />
                                </IconButton>
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
