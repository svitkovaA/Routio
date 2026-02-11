import TextField from "@mui/material/TextField";
import { ChangeEventHandler } from "react";

type OptionSelectProps = {
    label: string;
    value: string;
    onChange: ChangeEventHandler<HTMLInputElement | HTMLTextAreaElement>;
    setOption: (direction: number) => void;
    children: React.ReactNode;
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
