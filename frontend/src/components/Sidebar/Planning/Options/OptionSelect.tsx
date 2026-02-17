/**
 * @file OptionSelect.tsx
 * @brief Select input component
 * @author Andrea Svitkova (xsvitka00)
 */

import { ChangeEventHandler } from "react";
import TextField from "@mui/material/TextField";

type OptionSelectProps = {
    label: string;                                                          // Label displayed above the field
    value: string;                                                          // Currently selected value
    onChange: ChangeEventHandler<HTMLInputElement | HTMLTextAreaElement>;   // Change handler
    setOption: (direction: number) => void;                                 // Function for cycling through options
    children: React.ReactNode;                                              // Select menu items
};

function OptionSelect({
    label,
    value,
    onChange,
    setOption,
    children
} : OptionSelectProps) {
    return (
        <TextField
            select
            label={label}
            value={value}
            variant="outlined"
            onChange={onChange}
            onKeyDown={(event) => {
                if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                    event.preventDefault();
                    const direction = event.key === "ArrowDown" ? 1 : -1;
                    setOption(direction);
                }
            }}
            slotProps={{
                inputLabel: { shrink: true },
                select: {
                    MenuProps: {
                        PaperProps: {
                            sx: {
                                "& .MuiMenuItem-root:hover": {
                                    backgroundColor: "var(--color-item-hover)",
                                },
                                "& .MuiMenuItem-root.Mui-selected": {
                                    backgroundColor: " var(--color-item-selected) !important",
                                },
                                "& .MuiMenuItem-root.Mui-selected:hover": {
                                    backgroundColor: "var(--color-item-hover) !important",
                                },
                            }
                        }
                    }
                }
            }}
        >
            {children}
        </TextField>
    );
}

export default OptionSelect;

/** End of file OptionSelect.tsx */
