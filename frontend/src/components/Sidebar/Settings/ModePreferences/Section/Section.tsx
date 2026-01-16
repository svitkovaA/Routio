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
        setValue(Number(e.target.value));
    };

    return(
        <div className="section">
            <span className="section-label">
                {label}
            </span>
            <TextField
                type="number"
                value={value}
                onChange={handleChange}
                className="number-input"
                slotProps={{
                    htmlInput: {
                        ...bounds,
                        step: 1,
                    },
                    input: {
                        endAdornment: (
                            <InputAdornment position="end" style={{ display: 'flex', gap: '4px' }}>

                                {/* Decrease value button */}
                                <IconButton
                                    onClick={() => setValue(prev => Math.max(0, prev - 1))}
                                    size="small"
                                >
                                    <RemoveIcon fontSize="small" />
                                </IconButton>

                                {/* Increase value button */}
                                <IconButton
                                    onClick={() => setValue(prev => Math.min(10, prev + 1))}
                                    size="small"
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
