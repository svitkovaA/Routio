import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import TextField from "@mui/material/TextField";
import "./Section.css";

type SectionProps = {
    label: string;
    value: number;
    setValue: (value: number | ((prev: number) => number)) => void;
    bounds: { min: number, max: number };
}

function Section({
    label,
    value,
    setValue,
    bounds
} : SectionProps) {

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
                                <IconButton
                                    onClick={() => setValue(prev => Math.max(0, prev - 1))}
                                    size="small"
                                >
                                    <RemoveIcon fontSize="small" />
                                </IconButton>

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